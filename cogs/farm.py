import logging
from datetime import timedelta, datetime
from math import log10

import discord, schedule
from discord.ext import commands

from config import *
from messages.farm import *
from messages.core import MSG_CMD_INVALID
from objects.economy.account import EconomyAccount
from objects.economy.farm.farm import Farm as ORMFarm
from objects.economy.farm.plant import Plant
from objects.economy.farm.pricelog import PriceLog
from objects.economy.farm.upgrade import Upgrade
import utils.numbers as numutils


class Farm(commands.Cog):
    def  __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["f"])
    async def farm(self, ctx, target: discord.Member=None):
        """Show target's farm details."""
        if target is None:
            target = ctx.author
        _farm = ORMFarm.get_farm(target, self.bot.db_session)
        
        farm_name = _farm.get_name(self.bot.db_session)

        embed = discord.Embed(
            title="{0.name}#{0.discriminator}'s farm, {1}".format(target, farm_name),
            color=0xffd700
        )

        embed.add_field(name="Plots", value=numutils.millify(len(_farm.plots)))
        embed.add_field(
            name="Storage", 
            value="{0}/{1}".format(
                numutils.millify(_farm.current_harvest), numutils.millify(_farm.get_harvest_capacity())
            ),
        )

        embed.add_field(name="Harvest Multiplier", value="{0:.3f}x".format(_farm.get_harvest_multiplier()), inline=False)
        embed.add_field(name="Prices Multiplier", value="{0:.3f}x".format(_farm.get_price_multiplier()), inline=False)
        embed.add_field(name="Storage Multiplier", value="{0:.3f}x".format(_farm.get_storage_multiplier()), inline=False)

        for _upgrade in _farm.upgrades:
            val = _upgrade.level
            embed.add_field(name=_upgrade.name.capitalize(), value=val)

        await ctx.send(embed=embed)

    @commands.command(aliases=["ftop"])
    async def farmtop(self, ctx):
        """Shows top farms in the server."""
        top_farms = ORMFarm.get_top_farms(self.bot.db_session)

        embed = discord.Embed(title="Top 10 Most Bountiful Farms", color=0xffd700)
        rank = 1
        for _farm in top_farms:
            plot_count = len(_farm.plots)
            leaf_count = int(log10(plot_count))+1
            user = self.bot.get_user(_farm.user_id)
            try:
                row_name = "#{1} **{2}** - ({0.name}#{0.discriminator})".format(user, rank, _farm.get_name(self.bot.db_session))
            except AttributeError:
                row_name = "#{1} **{2}** - ({0})".format("Unknown User", rank, _farm.get_name(self.bot.db_session))
            plot_count = "🌱"*leaf_count + " {0} Plots".format(numutils.millify(len(_farm.plots)))
            embed.add_field(name=row_name, value=plot_count, inline=False)
            rank += 1

        await ctx.send(embed=embed)

    @commands.command()
    async def setfarmname(self, ctx, name):
        """Show target's farm details."""
        if len(name) > 32:
            await ctx.send(MSG_FARM_RENAME_NAME_TOO_LONG.format(ctx.author))
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        _farm.name = name
        _account = EconomyAccount.get_economy_account(ctx.author, self.bot.db_session)

        if not _account.has_balance(FARM_NAME_CHANGE_PRICE, raw=True):
            await ctx.send(MSG_INSUFFICIENT_FUNDS_EXTRA.format(
                ctx.author, numutils.millify(_account.get_balance(), is_money=True), FARM_NAME_CHANGE_PRICE / 10000
            ))
            return

        _account.add_debit(
            self.bot.db_session, FARM_NAME_CHANGE_PRICE, 
            name="FARM NAME CHANGE", raw=True
        )

        self.bot.db_session.add(_farm)
        self.bot.db_session.commit()
        
        await ctx.send(MSG_FARM_RENAME_SUCCESS.format(
            ctx.author, name, numutils.millify(_account.get_balance(), is_money=True)
        ))

    @commands.command(aliases=["u$"])
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def upgradeprice(self, ctx, upgrade_name=None, up_count: int=1):
        """Check upgrade prices. You can specify an upgrade count <= 1M."""
        up_count = max(1, up_count)
        up_count = min(1000000, up_count)
        if upgrade_name is None:
            embed = discord.Embed(
                title="{0.name}#{0.discriminator}'s Upgrade Prices".format(ctx.author),
                color=0xffd700
            )
            _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
            for _upgrade in _farm.upgrades:
                embed.add_field(
                    name=_upgrade.name.capitalize(),
                    value="`{0} gil`".format(numutils.millify(_upgrade.get_next_level_cost(raw=False), is_money=True))
                )
            await ctx.send(embed=embed)
        else:
            upgrade_name = upgrade_name.lower()
            if upgrade_name not in FARM_UPGRADES:
                await ctx.send(MSG_CMD_INVALID.format(ctx.author))
                return
            _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
            upgrade_cost = _farm.get_upgrade_cost(upgrade_name, up_count=up_count)
            await ctx.send("{0.mention}, your next {3} **{1}** upgrades costs **💵 {2}** gil.".format(
                ctx.author, upgrade_name.capitalize(), numutils.millify(upgrade_cost), up_count
            ))

    @commands.command(aliases=["ubuy"])
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def upgradebuy(self, ctx, upgrade_name=None, up_count: int=1):
        """Buy an upgrade (up to 1M upgrades)."""
        up_count = max(1, up_count)
        up_count = min(1000000, up_count)
        if upgrade_name is None:
            await ctx.send(MSG_CMD_INVALID.format(ctx.author))
            return
        upgrade_name = upgrade_name.lower()
        if upgrade_name not in FARM_UPGRADES:
            await ctx.send(MSG_CMD_INVALID.format(ctx.author))
            return
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        _account = EconomyAccount.get_economy_account(ctx.author, self.bot.db_session)

        upgrade_cost = _farm.get_upgrade_cost(upgrade_name, raw=True, up_count=up_count)

        if not _account.has_balance(upgrade_cost, raw=True):
            await ctx.send(MSG_INSUFFICIENT_FUNDS_EXTRA.format(
                ctx.author, numutils.millify(_account.get_balance(), is_money=True), numutils.millify(upgrade_cost / 10000, is_money=True)
            ))
            return
        
        _farm.upgrade(self.bot.db_session, upgrade_name, up_count)
        _account.add_debit(self.bot.db_session, upgrade_cost,
            name="U:{}".format(upgrade_name), raw=True
        )
        
        await ctx.send("{0.mention}, you bought {4} **{1} upgrades** for **💵 {3}** gil. You now only have **💵 {2}** gil.".format(
            ctx.author, upgrade_name, numutils.millify(_account.get_balance(), is_money=True),
            numutils.millify(upgrade_cost / 10000, is_money=True),
            up_count
        ))

    @commands.command(aliases=["fp"])
    async def farmplots(self, ctx, page_number: int=1):
        """Show the details of your plots."""
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        _plots = _farm.get_all_plots(self.bot.db_session)

        plot_count = len(_plots)

        paginated_plots = [
            _plots[i:i+20] for i in range(0, plot_count, 20)
        ]

        # Make sure page number is in bounds
        page_number = min(page_number, len(paginated_plots))
        page_number = max(page_number, 1)
        
        plot_str = ""
        plot_count = 1 + (20 * (page_number-1))
        for _plot in paginated_plots[page_number-1]:
            plot_str += "Plot #{0:04d}: {1}\n".format(plot_count, _plot.get_status_str())
            plot_count += 1
        
        embed = discord.Embed(
            title="{0.name}#{0.discriminator}'s farm, {1}".format(ctx.author, _farm.name),
            color=0xffd700
        )

        embed.add_field(
            name=MSG_PLOTS_STATUS.format(page_number, len(paginated_plots)),
            value="```{}```".format(plot_str)
        )

        embed.set_footer(text="Showing 20 plots per page. s!fp [page_number]")

        await ctx.send(embed=embed)

    @commands.command(aliases=["p$",])
    async def plantprices(self, ctx, plant_name=None):
        """Show the current global plant prices."""
        try:
            page_number = int(plant_name)
            plant_name = None
        except TypeError:
            page_number = 1
        except ValueError:
            _plant = Plant.get_plant(self.bot.db_session, plant_name)

        if plant_name is not None:
            _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
            
            if _plant is None:
                await ctx.send(MSG_PLANT_NOT_FOUND.format(ctx.author))
                return

            embed = discord.Embed(
                title="-=Current {0} Market Prices=-".format(_plant.name),
                color=0xffd700
            )
            bp = numutils.millify(_plant.get_buy_price(), is_money=True)
            sp = numutils.millify(_plant.get_sell_price(), is_money=True)
            embed.add_field(
                name="**`{0.tag}` - {0.name}**".format(_plant),
                value=MSG_PLANT_PRICES.format(
                  [numutils.millify(_plant.current_demand), numutils.millify(_plant.base_demand), _plant.base_harvest], 
                  bp, sp, get_growing_time_string(_plant.growing_seconds)  
                ) + 
                "\nYour price: `{0} gil`".format(numutils.millify(_plant.get_farm_sell_price(_farm), is_money=True)) +
                "\nYour yield: **{0}** units".format(numutils.millify(_plant.get_farm_yield(_farm))),
                inline=False
            )
        else:
            all_plants = Plant.get_plants(self.bot.db_session)

            plant_count = len(all_plants)

            paginated_plants = [
                all_plants[i:i+10] for i in range(0, plant_count, 10)
            ]

            # Make sure page number is in bounds
            page_number = min(page_number, len(paginated_plants))
            page_number = max(page_number, 1)

            embed = discord.Embed(
                title="-=Current Global Market Prices=-\nPage {0} of {1}".format(
                    page_number, len(paginated_plants)
                ),
                color=0xffd700
            )

            final_str = ""
            for _plant in paginated_plants[page_number-1]:
                bp = numutils.millify(_plant.get_buy_price(), is_money=True)
                sp = numutils.millify(_plant.get_sell_price(), is_money=True)
                embed.add_field(
                    name="**`{0.tag}` - {0.name}**".format(_plant),
                    value=MSG_PLANT_PRICES.format(
                    [numutils.millify(_plant.current_demand), numutils.millify(_plant.base_demand), _plant.base_harvest], 
                    bp, sp, get_growing_time_string(_plant.growing_seconds)  
                    ),
                    inline=False
                )
            embed.set_footer(
                text=MSG_PLANT_PRICES_FOOTER.format(
                    (timedelta(hours=1) + datetime.now().replace(
                        microsecond=0, second=0, minute=0)).strftime("%I:%M %p UTC+08:00")    
                )
            )
        await ctx.send(embed=embed)

    @commands.command(aliases=["plot$",])
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def plotprice(self, ctx, up_count: int=1):
        """Show the price of the next N plots. (N <= 1M)"""
        up_count = max(1, up_count)
        up_count = min(1000000, up_count)
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        result = _farm.get_next_plot_price(up_count=up_count)
        await ctx.send(MSG_PLOT_PRICE_CHECK.format(ctx.author, numutils.millify(result, is_money=True)))

    @commands.command()
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def plotbuy(self, ctx, up_count: int=1):
        """Buy new N plots. (N <= 1M)"""
        up_count = max(1, up_count)
        up_count = min(1000000, up_count)
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        _account = EconomyAccount.get_economy_account(ctx.author, self.bot.db_session)
        price = _farm.get_next_plot_price(raw=True, up_count=up_count)
        if _account.has_balance(price, raw=True):
            _farm.add_plot(self.bot.db_session, up_count=up_count)
            _account.add_debit(self.bot.db_session, price, name="PLOTBUY", raw=True)
            await ctx.send(MSG_PLOT_BUY_SUCCESS.format(
                ctx.author, numutils.millify(_account.get_balance(), is_money=True),
                up_count
            ))
        else:
            await ctx.send(MSG_INSUFFICIENT_FUNDS_EXTRA.format(
                ctx.author, numutils.millify(_account.get_balance(), is_money=True),
                numutils.millify(price / 10000, is_money=True)
            ))

    @commands.command(aliases=["silo$",])
    async def siloprice(self, ctx):
        """Show the price of the next silo (storage upgrade)."""
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        result = _farm.get_next_storage_upgrade_price()
        await ctx.send(MSG_SILO_PRICE_CHECK.format(ctx.author, numutils.millify(result, is_money=True)))

    @commands.cooldown(1, 1, type=commands.BucketType.user)
    @commands.command()
    async def silobuy(self, ctx):
        """Buy a new silo (increases your storage by 100)."""
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        _account = EconomyAccount.get_economy_account(ctx.author, self.bot.db_session)
        price = _farm.get_next_storage_upgrade_price(raw=True)
        if _account.has_balance(price, raw=True):
            _farm.upgrade_storage(self.bot.db_session)
            _account.add_debit(self.bot.db_session, price, name="SILOBUY", raw=True)
            await ctx.send(MSG_SILO_BUY_SUCCESS.format(ctx.author, numutils.millify(_account.get_balance(), is_money=True)))
        else:
            await ctx.send(MSG_INSUFFICIENT_FUNDS.format(ctx.author, numutils.millify(_account.get_balance(), is_money=True)))

    @commands.command()
    @commands.is_owner()
    async def setplanttag(self, ctx, plant_name, tag):
        """(Owner) Set a plant's shorthand tag."""
        _plant = Plant.get_plant(self.bot.db_session, plant_name)
        if _plant is None:
            await ctx.send(MSG_PLANT_NOT_FOUND.format(ctx.author))
            return
        _plant.tag = tag
        self.bot.db_session.add(_plant)
        self.bot.db_session.commit()
        await ctx.send("**Successfully changed plant tag.**")
    
    @commands.command()
    @commands.is_owner()
    async def setplantprice(self, ctx, plant_name, base_price: float):
        """(Owner) Set a plant's base unit price."""
        _plant = Plant.get_plant(self.bot.db_session, plant_name)
        if _plant is None:
            await ctx.send(MSG_PLANT_NOT_FOUND.format(ctx.author))
            return
        _plant.set_base_price(self.bot.db_session, base_price)

    @commands.command()
    @commands.is_owner()
    async def purgeplots(self, ctx, target: discord.Member=None):
        """(Owner) Purge the plants planted in a target's plots."""
        if target == None:
            target = ctx.author
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        for _plot in _farm.plots:
            _plot.plant = None
            _plot.planted_at = None
            self.bot.db_session.add(_plot)
        self.bot.db_session.add(_plot)
        await ctx.send("**{0.mention}'s plots have been purged.**".format(target))
    
    @commands.command()
    async def trashplots(self, ctx, scrap_range=None):
        """Discard the plants on your plots. No refunds.
        Scrap range can be:
        - a number, to scrap that single plot
        - a range (1-4, 5-7, etc.) with NO SPACES to scrap those plots, the numbers included
        You can also choose to leave the scrap_range blank, to scrap ALL your plots.
        """
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        plot_count = len(_farm.plots)

        all_plots = False

        if scrap_range is not None:
            try:
                scrap_range = list(map(int, scrap_range.split('-')))  
            except ValueError:
                await ctx.send(MSG_CMD_INVALID.format(ctx.author))
                return
        else:
            all_plots = True
            scrap_range = [1, plot_count]
        
        # Command validation:
        if len(scrap_range) > 2:
            await ctx.send(MSG_CMD_INVALID.format(ctx.author))
            return
        
        if len(scrap_range) == 1:
            scrap_range.append(scrap_range[0])

        if scrap_range[1] < scrap_range[0]:
            await ctx.send(MSG_CMD_INVALID.format(ctx.author))
            return
        
        if not (0 <= scrap_range[0]-1 < plot_count) or not (0 <= scrap_range[1]-1 < plot_count):
            await ctx.send(MSG_DISCARD_OUT_OF_RANGE.format(ctx.author))
            return
        
        for i in range(scrap_range[0]-1, scrap_range[1]):
            _farm.plots[i].plant = None
            _farm.plots[i].planted_at = None
            self.bot.db_session.add(_farm.plots[i])
        self.bot.db_session.commit()

        if all_plots:
            await ctx.send(MSG_DISCARD_ALL.format(ctx.author))
        elif scrap_range[0] == scrap_range[1]:
            await ctx.send(MSG_DISCARD_SINGLE.format(ctx.author, scrap_range))
        else:
            await ctx.send(MSG_DISCARD_RANGE.format(ctx.author, scrap_range))
    
    @commands.command()
    @commands.is_owner()
    async def reconsolidatestorage(self, ctx):
        """(Owner) Manually reconsolidate all farm capacities."""
        all_farms = ORMFarm.get_all_farms(self.bot.db_session)
        for _farm in all_farms:
            harvest_count = 0
            for _harvest in _farm.harvests:
                harvest_count += _harvest.amount
            _farm.current_harvest = harvest_count
            self.bot.db_session.add(_farm)
        self.bot.db_session.commit()
        logging.info("Reconsolidated storages of {} farms.".format(len(all_farms)))
        await ctx.send("**All farm storages reconsolidated!**")
    
    @commands.command(aliases=['rpp',])
    @commands.is_owner()
    async def refreshplantprices(self, ctx):
        """(Owner) Manually refresh the global market prices."""
        all_plants = Plant.get_plants(self.bot.db_session)
        for plant in all_plants:
            plant.randomize_price(self.bot.db_session)
        final_str = ""
        for plant in all_plants:
            bp = numutils.millify(plant.get_buy_price(), is_money=True)
            sp = numutils.millify(plant.get_sell_price(), is_money=True)
            _str = "***{0.name}*** `[B: {1} gil | S: {2} gil]`\n".format(plant, bp, sp)
            final_str += _str
        await ctx.send("**Prices refreshed!**\n{}".format(final_str))

    @commands.command(aliases=["fpa"])
    async def farmplant(self, ctx, plant_name, plant_count=1):
        """Plant a crop on a number of your available plots."""
        _plant = Plant.get_plant(self.bot.db_session, plant_name)
        if _plant is None:
            await ctx.send(MSG_PLANT_NOT_FOUND.format(ctx.author))
            return
        _account = EconomyAccount.get_economy_account(ctx.author, self.bot.db_session)
        
        total_price = _plant.buy_price * plant_count
        
        if not _account.has_balance(total_price, raw=True):
            await ctx.send(MSG_INSUFFICIENT_FUNDS_EXTRA.format(
                ctx.author, numutils.millify(_account.get_balance(), is_money=True),
                numutils.millify(total_price / 10000, is_money=True)
            ))
            return
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        _plots = _farm.get_available_plots(self.bot.db_session)
        if len(_plots) == None:
            await ctx.send(MSG_PLOT_NOT_FOUND.format(ctx.author))
            return
        if len(_plots) < plant_count:
            await ctx.send(MSG_PLANT_NO_PLOTS.format(ctx.author, len(_plots), plant_count))
            return

        _account.add_debit(
            self.bot.db_session, total_price,
            name="B:{0.id}={0.buy_price}".format(_plant),
            raw=True,
        )

        for _plot in _plots[:plant_count]:
            _plot.plant_to_plot(_plant, self.bot.db_session, commit_on_execution=False)
        self.bot.db_session.commit()

        await ctx.send(
            MSG_PLOT_PLANT.format(
                ctx.author, _plant,
                plant_count, numutils.millify(total_price/10000),
                numutils.millify(_account.get_balance(), is_money=True)
            )
        )

    @commands.command(aliases=["sh"])
    async def showharvests(self, ctx):
        """Show your harvest inventory."""
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        
        harvested_plants = set([i.plant for i in _farm.harvests])
        print(_farm.harvests)

        id_to_plant_name = {_plant.id: _plant.name for _plant in harvested_plants}
        total_harvests = {_plant.id: 0 for _plant in harvested_plants}

        if len(_farm.harvests) == 0:
            await ctx.send(MSG_SHOW_HARVESTS_NONE.format(ctx.author))
            return

        for harvest in _farm.harvests:
            total_harvests[harvest.plant.id] += harvest.amount

        harvest_str = ""

        embed = discord.Embed(
            title="{0.name}#{0.discriminator}'s Harvests".format(ctx.author),
            color=0xffd700
        )

        for harvest in total_harvests:
            harvest_str += "**{0}**, {1} units\n".format(
                id_to_plant_name[harvest],
                numutils.millify(total_harvests[harvest])
            )

        embed.add_field(name="Crops", value=harvest_str, inline=False)
        
        # await ctx.send(MSG_SHOW_HARVESTS.format(ctx.author, harvest_str))
        await ctx.send(embed=embed)

    @commands.command(aliases=["fh"])
    async def farmharvest(self, ctx, harvest_range=None):
        """Harvest all your harvestable crops."""
        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        plot_count = len(_farm.plots)

        all_plots = False

        if harvest_range is not None:
            try:
                harvest_range = list(map(int, harvest_range.split('-')))  
            except ValueError:
                await ctx.send(MSG_CMD_INVALID.format(ctx.author))
                return
        else:
            all_plots = True
            harvest_range = [1, plot_count]
        
        # Command validation:
        if len(harvest_range) > 2:
            await ctx.send(MSG_CMD_INVALID.format(ctx.author))
            return
        
        if len(harvest_range) == 1:
            harvest_range.append(harvest_range[0])

        if harvest_range[1] < harvest_range[0]:
            await ctx.send(MSG_CMD_INVALID.format(ctx.author))
            return
        
        if not (0 <= harvest_range[0]-1 < plot_count) or not (0 <= harvest_range[1]-1 < plot_count):
            await ctx.send(MSG_DISCARD_OUT_OF_RANGE.format(ctx.author))
            return

        storage_needed = 0
        for i in range(harvest_range[0]-1, harvest_range[1]):
            storage_needed += _farm.plots[i].get_harvest_amount()

        if not _farm.has_storage(storage_needed):
            await ctx.send(MSG_HARVEST_NOT_ENOUGH_CAPACITY.format(
                ctx.author,
                max(_farm.get_harvest_capacity() - _farm.current_harvest, 0),
                storage_needed
            ))
            return

        # Actual harvesting
    
        harvest_stats = {}
        has_harvest = False

        for i in range(harvest_range[0]-1, harvest_range[1]):
            _harvest = _farm.plots[i].harvest(self.bot.db_session, commit_on_execution=False)
            if _harvest is None:
                continue

            has_harvest = True
            if _harvest.plant.name not in harvest_stats:
                harvest_stats[_harvest.plant.name] = 0
            harvest_stats[_harvest.plant.name] += _harvest.amount

        self.bot.db_session.commit()

        if has_harvest:
            harvest_str = ""
            for plant_name in harvest_stats:
                harvest_str += "**{0}**, {1} units\n".format(
                    plant_name, numutils.millify(harvest_stats[plant_name])
                )
            await ctx.send(MSG_HARVEST_SUCCESS.format(ctx.author, harvest_str))
        else:
            await ctx.send(MSG_HARVEST_NONE.format(ctx.author))
        

    @commands.command(aliases=["pstats", "pstat"])
    async def plantstats(self, ctx, plant_name):
        """Check plant price stats for the past 48 refreshes."""
        _plant = Plant.get_plant(self.bot.db_session, plant_name)
        if _plant is None:
            await ctx.send(MSG_PLANT_NOT_FOUND.format(ctx.author))
            return
        logging.info(PriceLog.get_plant_price_logs(_plant, self.bot.db_session))

    @commands.command(aliases=["fs"])
    async def farmsell(self, ctx, plant_name):
        """Sell all of your target crop."""
        _plant = Plant.get_plant(self.bot.db_session, plant_name)
        if _plant is None:
            await ctx.send(MSG_PLANT_NOT_FOUND.format(ctx.author))
            return

        _farm = ORMFarm.get_farm(ctx.author, self.bot.db_session)
        _account = EconomyAccount.get_economy_account(ctx.author, self.bot.db_session)

        total_amount = 0
        total_raw_amount = 0
        for i in range(len(_farm.harvests))[::-1]:
            if _farm.harvests[i].plant.id == _plant.id:
                total_amount += _farm.harvests[i].amount
                total_raw_amount += _plant.base_harvest
                del _farm.harvests[i]

        if total_amount == 0:
            await ctx.send(MSG_SELL_NONE.format(ctx.author, _plant.name))
            return
        
        plant_sell_price = _plant.get_farm_sell_price(_farm, raw=True)
        raw_credit = total_amount * plant_sell_price
        _account.add_credit(
            self.bot.db_session, raw_credit,
            name="S:{0.id}={1}".format(_plant, total_amount),
            raw=True
        )
        
        logging.info(total_raw_amount)
        _plant.decrement_demand(self.bot.db_session, total_raw_amount)
        _farm.decrease_storage(self.bot.db_session, total_amount)

        await ctx.send(MSG_SELL_SUCCESS.format(
            ctx.author, numutils.millify(total_amount), _plant, numutils.millify(raw_credit / 10000, is_money=True),
            numutils.millify(_account.get_balance(), is_money=True),
            numutils.millify(plant_sell_price / 10000, is_money=True)
        ))


def get_growing_time_string(growing_time_in_seconds):
    growing_time = timedelta(seconds=growing_time_in_seconds)
    result_str = []
    hours, rem = divmod(growing_time.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if growing_time.days:
        result_str.append("{}d".format(growing_time.days))
    if hours:
        result_str.append("{}h".format(hours))
    if minutes:
        result_str.append("{}m".format(minutes))
    if seconds:
        result_str.append("{}s".format(seconds))
    return ', '.join(result_str)


def refresh_prices(bot):
    logging.info("Refreshing farm market prices...")
    all_plants = Plant.get_plants(bot.db_session)
    for plant in all_plants:
        plant.randomize_price(bot.db_session, commit_on_execution=False)
    bot.db_session.commit()


def setup(bot):
    bot.add_cog(Farm(bot))
    schedule.every().hour.at(":00").do(refresh_prices, bot)
