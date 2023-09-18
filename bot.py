from discord import app_commands, Interaction, File
from v2enlib import GSQLClass
from discord.ext import tasks
from math import ceil
from v2enlib import config

import io, os


class BaoBai:
    __name__ = "BaoBai"
    subjects_name = [
        "Lý",
        "Công nghệ",
        "Sử",
        "Anh",
        "Hóa",
        "Văn",
        "Toán",
        "Sinh",
        "Địa",
        "Thể dục",
        "GDQP",
        "GDCD",
        "Tin",
    ]
    subjects = {i: {} for i in subjects_name}

    def __init__(self) -> None:
        self.tree = app_commands.Group(
            name="baobai", description="Truy vấn báo bài trên Google Sheet"
        )

        self.source = GSQLClass(config.baobai.link)

        # init looping events
        self.update.start()

        # init guessword
        self.botCommands()

    def updateData(self) -> None:
        for sheet in self.source:
            data = sheet.getAll()
            if "TUẦN" not in sheet.table.title or sheet.table.isSheetHidden:
                continue
            for j in range(1, sheet.col_len() - 1):
                thu = data[1][j].split("\n")[1][1:-1]
                for i in range(3, sheet.row_len()):
                    if data[i][j] in self.subjects_name:
                        try:
                            if data[i + 1][j] not in self.subjects[data[i][j]][thu]:
                                self.subjects[data[i][j]][thu].append(data[i + 1][j])
                        except KeyError:
                            self.subjects[data[i][j]][thu] = [data[i + 1][j]]

    @tasks.loop(seconds=config.baobai.update)
    async def update(self):
        self.updateData()

        w = ceil(os.get_terminal_size().columns / 3)
        print(f"{'-'*w}\n\t\tUpdated!\n{'-'*w}")

    def botCommands(self):
        @self.tree.command(name="all", description="Hiện tất cả báo bài của các môn")
        @app_commands.describe(so_tiet="Số tiết gần đây cần hiển thị (Mặc định: 5)")
        async def all(ctx: Interaction, so_tiet: int = 5):
            user_name = ctx.user.name
            output = ""
            for e in self.subjects.items():
                output += f"Đây là báo bài của môn {e[0]} trong {so_tiet} tiết gần đây"
                l_output = []
                for i in e[1].items():
                    t_output, passed = f"\n    {i[0]}\n", False
                    while i[1] and i[1][-1] == "":
                        i[1].pop()
                    for j in i[1]:
                        if any(x.isalpha() for x in j):
                            t_output += "".join(
                                f"        {z}\n" for z in j.split("\n") if z
                            )
                            passed = True
                    if passed:
                        l_output.append(t_output)
                output += "".join(iter(l_output[-so_tiet:]))
            file = File(io.StringIO(output), filename=f"{user_name}.yml")
            await ctx.response.send_message(file=file)

        def monHoc(mon: str):
            async def monHocSub(ctx: Interaction, so_tiet: int = 5):
                user_name = ctx.user.name
                output = (
                    f"Đây là báo bài của môn {mon.lower()} trong {so_tiet} tiết gần đây"
                )
                l_output = []
                for i in self.subjects[mon].items():
                    t_output, passed = f"\n    {i[0]}\n", False
                    while i[1] and i[1][-1] == "":
                        i[1].pop()
                    for j in i[1]:
                        if any(x.isalpha() for x in j):
                            t_output += "".join(
                                f"        {z}\n" for z in j.split("\n") if z
                            )
                            passed = True
                    if passed:
                        l_output.append(t_output)
                output += "".join(iter(l_output[-so_tiet:]))
                file = File(io.StringIO(output), filename=f"{user_name}.yml")
                await ctx.response.send_message(file=file)

            return monHocSub

        self.updateData()
        for name in self.subjects_name:
            self.tree.command(
                name=name.lower().replace(" ", "_"),
                description=f"Hiện tất cả báo bài của môn {name.lower()}",
            )(
                app_commands.describe(
                    so_tiet=f"Số tiết môn {name} gần đây cần hiển thị (Mặc định: 5)"
                )(monHoc(name))
            )
