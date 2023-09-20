from discord import app_commands, Interaction, Embed, Activity, ActivityType
from v2enlib import GSQLClass
from discord.ext import tasks
from v2enlib import config
from time import sleep


class BaoBai:
    __name__ = "BaoBai"
    subjects_name = [
        "Toán",
        "Lý",
        "Hóa",
        "Văn",
        "Anh",
        "Sinh",
        "Sử",
        "Địa",
        "Công nghệ",
        "Tin",
        "Thể dục",
        "GDQP",
        "GDCD",
    ]
    subjects = {i: {} for i in subjects_name}

    def __init__(self, bot) -> None:
        self.tree = app_commands.Group(
            name="baobai", description="Truy vấn báo bài trên Google Sheet"
        )
        self.bot = bot

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
        await self.bot.change_presence(
            activity=Activity(
                name="dữ liệu từ Google sheet", type=ActivityType.competing
            )
        )
        self.updateData()
        sleep(10)
        await self.bot.change_presence(
            activity=Activity(name="lệnh /baobai", type=ActivityType.competing)
        )

    @staticmethod
    def outputFormat(x):
        return (
            x.replace("*", "* ")
            .replace("  ", " ")
            .replace("* ", "")
            .replace("Dặn dò:", "")
            .replace("Dặn dò", "")
        )

    def botCommands(self):
        @self.tree.command(name="all", description="Hiện tất cả báo bài của các môn")
        @app_commands.describe(so_tiet="Số tiết gần đây cần hiển thị (Mặc định: 5)")
        async def all(ctx: Interaction, so_tiet: int = 5):
            outputEmbeds = []
            for e in list(self.subjects.items())[:10]:
                l_output = []
                for i in e[1].items():
                    t_output, passed = f"\n{i[0]}\n", False
                    while i[1] and i[1][-1] == "":
                        i[1].pop()
                    for j in i[1]:
                        if any(x.isalpha() for x in j):
                            t_output += "".join(
                                f"{self.outputFormat(z)}\n" for z in j.split("\n") if z
                            )
                            passed = True
                    if passed:
                        l_output.append(t_output.replace("\n\n", "\n"))
                outputEmbeds.append(
                    Embed(title=e[0], description="".join(iter(l_output[-so_tiet:])))
                )
            await ctx.response.send_message(
                content=f"Đây là báo bài của các môn trong {so_tiet} tiết gần đây",
                embeds=outputEmbeds,
                ephemeral=True,
                delete_after=36000,
            )

        def monHoc(mon: str):
            async def monHocSub(ctx: Interaction, so_tiet: int = 5):
                l_output = []
                for i in self.subjects[mon].items():
                    t_output, passed = f"\n{i[0]}\n", False
                    while i[1] and i[1][-1] == "":
                        i[1].pop()
                    for j in i[1]:
                        if any(x.isalpha() for x in j):
                            t_output += "".join(
                                f"{self.outputFormat(z)}\n" for z in j.split("\n") if z
                            )
                            passed = True
                    if passed:
                        l_output.append(t_output.replace("\n\n", "\n"))
                await ctx.response.send_message(
                    embed=Embed(
                        title=f"Đây là báo bài của môn {mon.lower()} trong {so_tiet} tiết gần đây",
                        description="".join(iter(l_output[-so_tiet:])),
                    ),
                    ephemeral=True,
                    delete_after=36000,
                )

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
