import os
import random
import uuid
from twitchio.ext import commands
from twitchio import Channel, User
import csv
from typing import List, Dict
import math
import collections

class Bot(commands.Bot):
    # ----------INIT----------#
    def __init__(self):
        self.token = os.environ["IRC_TOKEN"]
        self.client_id = os.environ["CLIENT_ID"]
        self.nickname = os.environ["BOT_NICK"]
        self.prefix = os.environ["BOT_PREFIX"]
        self.initial_channels = [os.environ["CHANNEL"]]
        self.rankings = {}
        self.top_rankings = {"gold": "", "silver": "", "bronze": ""}
        self.moves_easy = {"punches": [4, "👊"], "kicks": [5, "🦶"], "bites": [5, "🦷"]}
        self.combos_easy = {"crescentkick": [10, "🦶🦶", "🦵"], "molarcrunch": [10, "🦷🦷", "👄"], "superpunch": [10, "👊👊", "💪"]}
        # self.moves_medium = {
        #     "backhand slaps": 8,
        #     "roundhouse kicks": 9,
        #     "headbutts": 10
        # }
        self.matches = {}
        self.contenders = []
        super().__init__(
            token=self.token, prefix=self.prefix, initial_channels=self.initial_channels
        )

    # ----------PREPARATION----------#
    async def event_ready(self):
        print(f"{self.nickname} HAS COMMENCED!")
        await bot.connected_channels[0].send(f"{self.nickname} HAS COMMENCED! 🥊")

    # async def event_message(self, message):
    #     if message.echo:
    #         return

    # async def event_join(self, channel: Channel, user: User):
    #     if user.name not in self.contenders:
    #         self.contenders.append(user.name)
    #         print(f'😄 {user.name} joined the stream!')

    # async def event_part(self, user: User):
    #     if user.name in self.contenders:
    #         self.contenders.remove(user.name)
    #         print(f'😕 {user.name} left the stream!')

    async def event_command_error(self, ctx, error: Exception) -> None:
        print("WHOOOPS!", error)
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                "SETTING UP NEXT MATCH. WAIT {:n} SECONDS. ⏲".format(
                    math.ceil(error.retry_after)
                )
            )

    # ----------COMMANDS----------#
    @commands.command()
    async def feature(self, ctx: commands.Context, arg=None, suggestion=None):
        if not arg:
            await ctx.send('USAGE: !feature ![cmd] "[suggestion]"')
            return

        if arg and not suggestion:
            await ctx.send(f"Recommend a feature for {arg}, homie.")
            return

        if arg and suggestion:
            self.append_to_features(arg, suggestion)
            await ctx.send("Word. 🙏")
            return

    @commands.command() 
    async def help(self, ctx: commands.Context, arg=None):
        if not arg:
            await ctx.send("USAGE: !help ![cmd]")

        if arg == "!fight":
            await ctx.send(f"!fight @insert_name - Fight contender. | !leaderboard - Current tournament's leaderboard. | !leaderboardalltime - Overall championship's leaderboard.")

    @commands.command()
    async def leaderboard(self, ctx: commands.Context):
        rank = sorted(self.rankings.items(), key=lambda x: x[1], reverse=True)[:3]
        print(self.rankings)
        print(rank)
        leaders = [("", "")] * 3
        for i in range(len(rank)):
            leaders[i] = rank[i]
        gold = leaders[0][0] if leaders[0][0] != "" else "NA"
        silver = leaders[1][0] if leaders[1][0] != "" else "NA"
        bronze = leaders[2][0] if leaders[2][0] != "" else "NA"
        self.top_rankings["gold"] = gold
        self.top_rankings["silver"] = silver
        self.top_rankings["bronze"] = bronze
        await ctx.send(
            f'🥇: {self.top_rankings["gold"]}, 🥈: {self.top_rankings["silver"]}, 🥉: {self.top_rankings["bronze"]}'
        )

    @commands.command()
    async def leaderboardalltime(self, ctx: commands.Context):
        prelim_rank = []

        # Read existing data
        if os.path.exists("botfighter.csv"):
            with open("botfighter.csv", "r", newline="") as file:
                reader = csv.DictReader(file)
                prelim_rank = list(reader)

        rank = sorted(
            [(item["fighter"], int(item["wins"])) for item in prelim_rank],
            key=lambda x: x[1],
            reverse=True,
        )[:3]
        leaders = [("", "")] * 3
        for i in range(len(rank)):
            leaders[i] = rank[i]
        gold = leaders[0][0] if leaders[0][0] != "" else "NA"
        silver = leaders[1][0] if leaders[1][0] != "" else "NA"
        bronze = leaders[2][0] if leaders[2][0] != "" else "NA"
        self.top_rankings["gold"] = gold
        self.top_rankings["silver"] = silver
        self.top_rankings["bronze"] = bronze
        await ctx.send(
            f'🥇: {self.top_rankings["gold"]}, 🥈: {self.top_rankings["silver"]}, 🥉: {self.top_rankings["bronze"]}'
        )

    # @commands.command()
    # async def check_matches(self, ctx):
    #     print(self.matches)
    #     print("---------------")
    #     output_dict = {key: value for inner_dict in self.matches.values() if isinstance(inner_dict, dict) for key, value in inner_dict.items() if isinstance(value, list)}
    #     # print(output_dict)
    #     print(output_dict)

    # @commands.command()
    # async def simulate_fight(self, ctx: commands.Context, arg):
    #     matchkey = self._get_matchkey(f'@{ctx.author.name}')
    #     # print(self.matches)
    #     # print(f'@{ctx.author.name}')
    #     # print(matchkey)
    #     return self._commence_fight(f'@{ctx.author.name}', arg, self.moves_easy, matchkey)
    @commands.cooldown(rate=1, per=3, bucket=commands.Bucket.channel)
    @commands.command()
    async def fight(self, ctx: commands.Context, arg = None):
        if arg == None:
            await ctx.send(f"CHOOSE YOUR OPPONENT! 🛑")
            return

        fighter = "@" + ctx.author.name.lower()
        versus = str(arg).lower()

        if versus == "@botfighterannouncer":
            await ctx.send("PLEASE DO NOT FIGHT THE ANNOUNCER! 🛑")
            return

        user = await ctx.bot.fetch_users(names=[versus.lstrip("@")])
        if not user:
            await ctx.send(f"PLEASE CHOOSE VALID CONTENDER! 🛑")
            return
        
        validatecheck, validatecode = (
            self._validate_fighters(fighter, versus)[0],
            self._validate_fighters(fighter, versus)[1],
        )

        if validatecheck != True:
            if validatecode == "conflict_versusbusy":
                await ctx.send(f"{versus} IS CURRENTLY FIGHTING. 🛑")
                return
            elif validatecode == "conflict_versuswrong":
                await ctx.send(f"{versus} IS NOT YOUR CURRENT OPPONENT. 🛑")
                return
            elif validatecode == "conflict_stophittingyourself":
                await ctx.send("STOP HITTING YOURSELF! 🛑")
                return
            elif validatecode == "conflict_chooseversus":
                await ctx.send("PLEASE CHOOSE YOUR OPPONENT! 🛑")
                return 
            
        if not self._get_matchkey(fighter):
            match_id = str(uuid.uuid1().hex)
            self.matches[match_id] = {}
            self._add_fighters_to_match(fighter, versus, match_id)
        else:
            match_id = self._get_matchkey(fighter)

        await ctx.send(f"💥 {fighter} VS {versus} 💥")
        self._select_round(fighter, versus, match_id)
        round = self.matches[match_id]["round"]
        commentary = self._commence_fight(fighter, versus, self.moves_easy, match_id)
        if round != 3:
            await ctx.send(f"ROUND {round} ... START! 🔔")
            await ctx.send(f"{commentary}")
        else:
            await ctx.send(f"FINAL ROUND ... START! 🔔")
            await ctx.send(f"{commentary}")
        if (
            round == 3
            or self.matches[match_id][fighter][1] == 2
            or self.matches[match_id][versus][1] == 2
        ):
            if self.matches[match_id][fighter][1] == 2:
                await ctx.send(f"{fighter} WINS! 🏆")
                if fighter not in self.rankings:
                    self.rankings[fighter] = 1
                    self._write_db("botfighter.csv", fighter)
                else:
                    self.rankings[fighter] += 1
                    self._write_db("botfighter.csv", fighter)
            else:
                await ctx.send(f"{versus} WINS! 🏆")
                if versus not in self.rankings:
                    self.rankings[versus] = 1
                    self._write_db("botfighter.csv", versus)
                else:
                    self.rankings[versus] += 1
                    self._write_db("botfighter.csv", versus)

            del self.matches[match_id]

    @commands.command()
    async def surrender(self, ctx: commands.Context):
        await ctx.send(f"@{ctx.author.name.lower()} SURRENDERS! 🏳")
        curr_matchkey = self._get_matchkey(f"@{ctx.author.name.lower()}")
        del self.matches[curr_matchkey]

    # ----------HELPERS----------#
    def _get_matchkey(self, fighter):
        match_key = "".join([k for k, v in self.matches.items() if f"{fighter}" in v])
        return match_key

    def _get_combo(self, cmbo):
        match_key = "".join([k for k, v in self.combos_easy.items() if f"{cmbo}" in v])
        return match_key

    def _add_fighters_to_match(self, fighter: str, versus: str, match_id: str):
        fhealth = 10
        vhealth = 10
        wins = 0

        self.matches[match_id] = {fighter: [fhealth, wins], versus: [vhealth, wins]}

    def _select_round(self, fighter: str, versus: str, match_id: str):
        round_limit = 3

        if "round" not in self.matches[match_id]:
            self.matches[match_id]["round"] = 1
        elif (
            "round" in self.matches[match_id]
            and self.matches[match_id]["round"] < round_limit
        ):
            self.matches[match_id]["round"] += 1
            self.matches[match_id][fighter][0] = 10
            self.matches[match_id][versus][0] = 10
        else:
            self.matches[match_id]["round"] = 1
            self.matches[match_id]["round"] = 1        
        
    def _validate_fighters(self, fighter, versus):
        print(versus, fighter)
        print(str(versus) == str(fighter))

        refined_matches = {
            key: value
            for inner_dict in self.matches.values()
            if isinstance(inner_dict, dict)
            for key, value in inner_dict.items()
            if isinstance(value, list)
        }

        if str(versus) == str(fighter):
            print("HELLO, LAVERNE!")
            return (False, "conflict_stophittingyourself")
        elif not isinstance(fighter, User) or not isinstance(versus, User):
            return (False, "conflict_notcontender")
        elif "@" not in str(versus) or "@" not in str(fighter):
            return (False, "conflict_notcontender")
        elif not versus:
            return (False, "conflict_chooseversus")
        elif (
            fighter in refined_matches
            and versus in refined_matches
            and self._get_matchkey(fighter) == self._get_matchkey(versus)
        ):
            return (True, "true_samematch")
        elif fighter not in refined_matches and versus not in refined_matches:
            return (True, "true_newmatch")
        elif (
            fighter in refined_matches
            and versus in refined_matches
            and self._get_matchkey(fighter) != self._get_matchkey(versus)
        ):
            return (False, "conflict_versusbusy")
        elif fighter not in refined_matches and versus in refined_matches:
            return (False, "conflict_versusbusy")
        elif fighter in refined_matches and versus not in refined_matches:
            return (False, "conflict_versuswrong")
        else:
            return

    def _commence_fight(self, fighter, versus, moveset, match_id, commentary="", atk_stk=None, mve_cnt = 1):
        fh = self.matches[match_id][fighter][0]
        vh = self.matches[match_id][versus][0]

        if not atk_stk:
            atk_stk = {}

        done = False

        if fh > 0 and vh > 0 and not done:
            prtcpts = [fighter, versus]  # as in, participants
            rand_ftr = random.choice(prtcpts)
            rand_atk = random.choice(list(moveset.keys()))
            rand_dmg = moveset[rand_atk][0]
            if prtcpts.index(rand_ftr) == 0:
                rand_dfs = prtcpts[1]
                self.matches[match_id][rand_dfs][0] -= rand_dmg
            else:
                rand_dfs = prtcpts[0]
                self.matches[match_id][rand_dfs][0] -= rand_dmg

            if rand_atk:
                atk = moveset[rand_atk][1]

            if rand_ftr not in atk_stk:
                atk_stk[rand_ftr] = [[atk, mve_cnt]]
                # print(atk)
            else:
                atk_stk[rand_ftr].append([atk, mve_cnt])
                # print(atk)

            commentary += (
                f"{rand_ftr} {atk} {rand_dfs} ({self.matches[match_id][rand_dfs][0]}). "
            )

            if self.matches[match_id][fighter][0] <= 0 or self.matches[match_id][versus][0] <= 0:
                done = True

            if not done:
                moves = [i for i in atk_stk.values()]
                p1moves = [j[0] for j in moves[0]]
                p1moveidx = [j[1] for j in moves[0]]
                # print("p1movesidx: ", p1moveidx)
                try:
                    p2moves = [k[0] for k in moves[1]]
                    p2moveidx = [k[1] for k in moves[1]]
                    # print("p2movesidx: ", p2moveidx)
                except IndexError:
                    p2moves = []
                    
                for cmbo in self.combos_easy.values():
                    cmbo_arr = [*cmbo[1]]
                    if any(cmbo_arr == list(x) for x in zip(*[p1moves[i:] for i in range(len(cmbo_arr))])) and p1moveidx[-1] - 1 == p1moveidx[-2]:
                        print(cmbo[1], cmbo[2])
                        self.matches[match_id][rand_dfs][0] -= cmbo[0]
                        commentary += (
                            f"{rand_ftr} {cmbo[2]} {rand_dfs} ({self.matches[match_id][rand_dfs][0]}). "
                        )
                    elif any(cmbo_arr == list(x) for x in zip(*[p2moves[i:] for i in range(len(cmbo_arr))])) and p2moveidx[-1] - 1 == p2moveidx[-2]:
                        print(cmbo[1], cmbo[2])
                        self.matches[match_id][rand_dfs][0] -= cmbo[0]
                        commentary += (
                            f"{rand_ftr} {cmbo[2]} {rand_dfs} ({self.matches[match_id][rand_dfs][0]}). "
                        )

        if fh <= 0:
            self.matches[match_id][versus][1] += 1
            commentary += f"😁{versus} KO'd 💀{fighter}!"
            # print(atk_stk)
            return commentary
        elif vh <= 0:
            self.matches[match_id][fighter][1] += 1
            commentary += f"😁{fighter} KO'd 💀{versus}!"
            # print(atk_stk)
            return commentary
        else:
            return self._commence_fight(fighter, versus, moveset, match_id, commentary, atk_stk, mve_cnt + 1)

    def _read_db(self, sheet):
        file = open(sheet, "r", encoding="utf8")
        reader = csv.DictReader(file)
        for r in reader:
            print(r)
        file.close()

    def _write_db(self, sheet, fighter):
        rows: List[Dict[str, int]] = []
        fighter = fighter.lower()
        if os.path.exists(sheet):
            with open(sheet, "r", newline="") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

        updated = False
        for row in rows:
            if row["fighter"] == fighter:
                row["wins"] = int(row["wins"]) + 1
                updated = True
                break

        if not updated:
            rows.append({"fighter": fighter, "wins": 1})

        with open(sheet, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["fighter", "wins"])
            writer.writeheader()
            writer.writerows(rows)

    def append_to_features(self, arg, feature):
        with open("features.txt", "a") as file:
            file.write(f"{arg} - {feature}\n")

bot = Bot()
bot.run()
