import os
import random
import uuid
from twitchio.ext import commands
import csv

class Bot(commands.Bot):
    #----------INIT----------#
    def __init__(self):
        self.token=os.environ['IRC_TOKEN']
        self.client_id = os.environ['CLIENT_ID']
        self.nickname=os.environ['BOT_NICK']
        self.prefix=os.environ['BOT_PREFIX']
        self.initial_channels=[os.environ['CHANNEL']]
        self.ranking = {}
        self.leaderboard={
            "gold": '',
            "silver": '',
            "bronze": ''
        }
        self.moves_easy = {
            "punches": 3,
            "kicks": 5,
            "bites": 4
        }
        self.matches = {}
        super().__init__(token=self.token, prefix=self.prefix, initial_channels=self.initial_channels)

    #----------PREPARATION----------#
    async def event_ready(self):
        print(f'{self.nickname} HAS COMMENCED!')
        await bot.connected_channels[0].send(f'{self.nickname} HAS COMMENCED! 🥊')

    # async def event_message(self, message):
    #     if message.echo:
    #         return
    #     await self.handle_commands(message)
        
    #----------COMMANDS----------#
    @commands.command()
    async def champions(self, ctx: commands.Context):
        rank = sorted(self.ranking.items(), key=lambda x: x[1], reverse=True)[:3]
        leaders = [('','')] * 3
        for i in range(len(rank)):
            leaders[i] = rank[i]
        gold = leaders[0][0] if leaders[0][0] != '' else 'NA'
        silver = leaders[1][0] if leaders[1][0] != '' else 'NA'
        bronze = leaders[2][0] if leaders[2][0] != '' else 'NA'
        self.leaderboard["gold"] = gold
        self.leaderboard["silver"] = silver
        self.leaderboard["bronze"] = bronze
        await ctx.send(f'🥇: {self.leaderboard["gold"]}, 🥈: {self.leaderboard["silver"]}, 🥉: {self.leaderboard["bronze"]}')

    # @commands.command()
    # async def check_matches(self, ctx):
    #     print(self.matches)

    # @commands.command()
    # async def simulate_fight(self, ctx: commands.Context, arg):
    #     matchkey = self._get_matchkey(f'@{ctx.author.name}')
    #     # print(self.matches)
    #     # print(f'@{ctx.author.name}')
    #     # print(matchkey)
    #     return self._commence_fight(f'@{ctx.author.name}', arg, self.moves_easy, matchkey)

    @commands.command()
    async def fight(self, ctx: commands.Context, arg):
        await ctx.send(f'💥 @{ctx.author.name} VS {arg} 💥')
        fighter = "@" + ctx.author.name
        versus = arg
        if not self._get_matchkey(fighter):
            match_id = str(uuid.uuid1().hex)
            self.matches[match_id] = {}
            self._add_fighters_to_match(fighter, versus, match_id)
        else:
            match_id = self._get_matchkey(fighter)
        
        self._select_round(fighter, versus, match_id)
        round = self.matches[match_id]['round']
        commentary = self._commence_fight(fighter, versus, self.moves_easy, match_id)
        if round != 3:
            await ctx.send(f'ROUND {round} ... START! 🔔')
            await ctx.send(f'{commentary}')
            # await ctx.send(f"🥋{fighter} KO'd 🥋{versus}!")
        else:
            await ctx.send(f'FINAL ROUND ... START! 🔔')
            await ctx.send(f'{commentary}')
            # await ctx.send(f"🥋{fighter} KO'd 🥋{versus}!")
        if round == 3 or self.matches[match_id][fighter][1] == 2 or self.matches[match_id][versus][1] == 2:
            if self.matches[match_id][fighter][1] == 2:
                await ctx.send(f'{fighter} WINS! 🏆')
                if fighter not in self.ranking:
                    self.ranking[fighter] = 1
                else:
                    self.ranking[fighter] += 1
            else:
                await ctx.send(f'{versus} WINS! 🏆')
                if versus not in self.ranking:
                    self.ranking[versus] = 1
                else:
                    self.ranking[versus] += 1
            
            del self.matches[match_id]

        # if fighter not in self.matches[match_id]:
        #     self._add_fighters_to_match(fighter, versus, match_id)
        #     self._select_round(fighter, versus, match_id)
        #     round = self.matches[match_id]['round']
        #     await ctx.send(f'ROUND {round} ... START! 🔔')
        #     # await ctx.send(f"👍 {fighter} KO's 👎 {versus}!")
        #     print(self.matches)
        #     return
        # elif fighter in self.matches[match_id] and self.matches[match_id]['round'] <= 3:
        #     self._select_round(fighter, versus)
        #     round = self.fights[fighter]['round']
        #     await ctx.send(f'ROUND {round} ... START! 🔔')
        #     # await ctx.send(f"👍 {fighter} KO's 👎 {versus}!")
        #     if round == 3:
        #         await ctx.send(f'{fighter} WINS! 🏆')
        #         print("RESET")
        #         del self.matches[match_id]
        #     print(self.matches)
        #     return
                
    @commands.command()
    async def surrender(self, ctx: commands.Context):
        await ctx.send(f'@{ctx.author.name} SURRENDERS! 🏳')
        curr_matchkey = self._get_matchkey(f'@{ctx.author.name}')
        del self.matches[curr_matchkey]   

    #----------HELPERS----------#
    def _get_matchkey(self, fighter):
        match_key = ''.join([k for k, v in self.matches.items() if f'{fighter}' in v])
        return match_key

    def _add_fighters_to_match(self, fighter: str, versus: str, match_id: str):
        fhealth = 10
        vhealth = 10
        wins = 0
        
        self.matches[match_id] = {
            fighter: [fhealth, wins],
            versus: [vhealth, wins]
        }

    def _select_round(self, fighter:str, versus: str, match_id: str):
        round_limit = 3
        # print(self.matches[match_id])

        if 'round' not in self.matches[match_id]:
            self.matches[match_id]['round'] = 1
            # print(self.matches[match_id])
        elif 'round' in self.matches[match_id] and self.matches[match_id]['round'] < round_limit:
            self.matches[match_id]['round'] += 1
            self.matches[match_id][fighter][0] = 10
            self.matches[match_id][versus][0] = 10
        else:
            self.matches[match_id]['round'] = 1
            self.matches[match_id]['round'] = 1

    def _commence_fight(self, fighter, versus, moveset, match_id, commentary=''):
        fh = self.matches[match_id][fighter][0]
        vh = self.matches[match_id][versus][0]
        fw = self.matches[match_id][fighter][1]
        vw = self.matches[match_id][versus][1]

        # print(self.matches[match_id])

        prtcpts = [fighter, versus] #as in, participants
        rand_ftr = random.choice(prtcpts)
        rand_atk = random.choice(list(moveset.keys()))
        rand_dmg = moveset[rand_atk]
        if prtcpts.index(rand_ftr) == 0:
            rand_dfs = prtcpts[1]
            self.matches[match_id][versus][0] -= rand_dmg
            # print("vh ", vh)
        else:
            rand_dfs = prtcpts[0]
            self.matches[match_id][fighter][0] -= rand_dmg
            # print("fh ", fh)

        if rand_atk == "kicks":
            atk = "🦵"
        elif rand_atk == "punches":
            atk = "👊"
        else:
            atk = "🦷"
        
        commentary += f'{rand_ftr} {atk} {rand_dfs}. '
        
        if fh <= 0:
            self.matches[match_id][versus][1] += 1
            commentary += f"😁{versus} KO'd 💀{fighter}!"
            return commentary
        elif vh <= 0:
            self.matches[match_id][fighter][1] += 1
            commentary += f"😁{fighter} KO'd 💀{versus}!"
            return commentary
        else:
            return self._commence_fight(fighter, versus, moveset, match_id, commentary)

bot = Bot()
bot.run()