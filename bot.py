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
        self.rankings = {}
        self.top_rankings={
            "gold": '',
            "silver": '',
            "bronze": ''
        }
        self.moves_easy = {
            "punches": [4, '👊'],
            "kicks": [6, '🦶'],
            "bites": [5, '🦷']
        }
        self.moves_medium = {
            "backhand slaps": 8,
            "roundhouse kicks": 9,
            "headbutts": 10
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
    async def leaderboard(self, ctx: commands.Context):
        rank = sorted(self.rankings.items(), key=lambda x: x[1], reverse=True)[:3]
        leaders = [('','')] * 3
        for i in range(len(rank)):
            leaders[i] = rank[i]
        gold = leaders[0][0] if leaders[0][0] != '' else 'NA'
        silver = leaders[1][0] if leaders[1][0] != '' else 'NA'
        bronze = leaders[2][0] if leaders[2][0] != '' else 'NA'
        self.top_rankings["gold"] = gold
        self.top_rankings["silver"] = silver
        self.top_rankings["bronze"] = bronze
        await ctx.send(f'🥇: {self.top_rankings["gold"]}, 🥈: {self.top_rankings["silver"]}, 🥉: {self.top_rankings["bronze"]}')

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

    @commands.command()
    async def fight(self, ctx: commands.Context, arg):
        fighter = "@" + ctx.author.name
        versus = arg
        # all_fighters = [key for inner_dict in self.matches.values() for key in inner_dict if key.startswith('@')]
        # # all_fighters = {k: v for k, v in self.matches.values()}
        # print(all_fighters)
        # fighter_idx = all_fighters.index(fighter) if fighter in all_fighters else -1
        # versus_idx = all_fighters.index(versus) if versus in all_fighters else -1
        # print(fighter_idx, versus_idx)

        # #scen1: if player fighting versus, can't fight other versus.
        # if fighter_idx != -1 and versus_idx != fighter_idx + 1:
        #     await ctx.send(f'YOU ARE BATTLING SOMEONE ELSE!')
        #     return
        # #scen2: if player tries to fight other in match:
        # if versus in all_fighters and versus_idx - 1 != fighter_idx:
        #     await ctx.send(f'{versus} IS CURRENTLY FIGHTING. 🛑')
        #     return 

        validatecheck, validatecode = self._validate_fighters(fighter, versus)[0], self._validate_fighters(fighter, versus)[1]
        print(self._validate_fighters(fighter, versus))
        if validatecheck != True:
            if validatecode == "conflict_versusbusy":
                await ctx.send(f'{versus} IS CURRENTLY FIGHTING. 🛑')
                return
            elif validatecode == "conflict_versuswrong":
                await ctx.send(f'{versus} IS NOT YOUR CURRENT OPPONENT. 🛑')
                return

        if not self._get_matchkey(fighter):
            match_id = str(uuid.uuid1().hex)
            self.matches[match_id] = {}
            self._add_fighters_to_match(fighter, versus, match_id)
        else:
            match_id = self._get_matchkey(fighter)
        
        await ctx.send(f'💥 @{ctx.author.name} VS {arg} 💥')
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
                if fighter not in self.rankings:
                    self.rankings[fighter] = 1
                else:
                    self.rankings[fighter] += 1
            else:
                await ctx.send(f'{versus} WINS! 🏆')
                if versus not in self.rankings:
                    self.rankings[versus] = 1
                else:
                    self.rankings[versus] += 1
            
            del self.matches[match_id]
                
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

    def _validate_fighters(self, fighter, versus):
        refined_matches = {key: value for inner_dict in self.matches.values() if isinstance(inner_dict, dict) for key, value in inner_dict.items() if isinstance(value, list)}
        
        if fighter in refined_matches and versus in refined_matches and self._get_matchkey(fighter) == self._get_matchkey(versus):
            return (True, "true_samematch")
        elif fighter not in refined_matches and versus not in refined_matches:
            return (True, "true_newmatch")
        elif fighter in refined_matches and versus in refined_matches and self._get_matchkey(fighter) != self._get_matchkey(versus):
            return (False, "conflict_versusbusy")
        elif fighter not in refined_matches and versus in refined_matches:
            return (False, "conflict_versusbusy")
        elif fighter in refined_matches and versus not in refined_matches:
            return (False, "conflict_versuswrong")

    def _commence_fight(self, fighter, versus, moveset, match_id, commentary=''):
        fh = self.matches[match_id][fighter][0]
        vh = self.matches[match_id][versus][0]

        # print(self.matches[match_id])
        if fh > 0 and vh > 0:
            prtcpts = [fighter, versus] #as in, participants
            rand_ftr = random.choice(prtcpts)
            rand_atk = random.choice(list(moveset.keys()))
            rand_dmg = moveset[rand_atk][0]
            if prtcpts.index(rand_ftr) == 0:
                rand_dfs = prtcpts[1]
                self.matches[match_id][rand_dfs][0] -= rand_dmg
                # print("vh ", vh)
            else:
                rand_dfs = prtcpts[0]
                self.matches[match_id][rand_dfs][0] -= rand_dmg
                # print("fh ", fh)

            if rand_atk:
                atk = moveset[rand_atk][1]
            
            commentary += f'{rand_ftr} {atk} {rand_dfs} ({self.matches[match_id][rand_dfs][0]}). '
        
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