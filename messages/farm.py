MSG_DISCARD_SINGLE = "**{0.mention}, `Plot #{1[0]:04d}` has been scrapped.**"
MSG_DISCARD_RANGE = "**{0.mention}, `Plot #{1[0]:04d}` to `Plot #{1[1]:04d}` have been scrapped.**"
MSG_DISCARD_ALL = "**{0.mention}, all your plots have been scrapped.**"
MSG_DISCARD_OUT_OF_RANGE = "**{0.mention}, the numbers you have chosen are not in the range of all your plots.**"
MSG_FARM_RENAME_NAME_TOO_LONG = "**{0.mention}, a farm's name can only be 32 characters long.**"
MSG_FARM_RENAME_SUCCESS = "{0.mention}, you successfully named your farm **{1}**. You now only have **💵 {2:,.2f} gil**"
MSG_FARM_STATUS = """{0.mention}'s farm: **{1.name}**
```
Plot count: {2}
```
"""
MSG_HARVEST_NOT_ENOUGH_CAPACITY = "{0.mention}, you do not have enough storage. You only have **{1}** available storage space for crops. You are trying to harvest a total of **{2}** units of crops. You can use `s!silobuy` to upgrade your storage."
MSG_HARVEST_NONE = "{0.mention}, you have no harvestable crops."
MSG_HARVEST_SUCCESS = "{0.mention}, you have successfully harvested your plots:\n{1}"
MSG_INSUFFICIENT_FUNDS = "{0.mention}, you do not have enough gil. You only have **💵 {1:,.2f} gil**"
MSG_INSUFFICIENT_FUNDS_EXTRA = "{0.mention}, you do not have enough gil. This operation costs **💵 {2:,.2f} gil**. You only have **💵 {1:,.2f} gil**"
MSG_PLANT_NOT_FOUND = "**{0.mention}, that plant is not in our database.**"
MSG_PLANT_NO_PLOTS = "**{0.mention}, you do not have enough available plots for that.** You only have **{1}** available and you're trying to plant on **{2}**."
MSG_PLANT_PRICES = "`[B: {1:,.2f} gil | (Demand: {0.current_demand}/{0.base_demand}) S: {2:,.2f} gil]`\nYields **{0.base_harvest}** units per harvest, grows in `{3}`"
MSG_PLANT_PRICES_FOOTER = "Next market recalculation will be at {0}"
MSG_PLOTS_STATUS = "Showing page **{0} of {1}**:\n"
# MSG_PLOTS_STATUS = "{0.mention}'s farm, **{1}**\nDisplaying 20 plots per page. Showing page **{3} of {4}**:\n```{2}```"
MSG_PLOT_NOT_FOUND = "**{0.mention}, you have no available plots to plant on.**"
MSG_PLOT_PLANT = "{0.mention}, you have planted **{1.name}** in {2} of your plots for **💵 {3:,.2f} gil**. You now only have **💵 {4:,.2f} gil**."
MSG_PLOT_PRICE_CHECK = "{0.mention}, your next **{2}** plots costs **💵 {1:,.2f} gil**."
MSG_PLOT_BUY_SUCCESS = "{0.mention}, you have successfully bought **{2}** new plots! Your new balance is now **💵 {1:,.2f} gil**."
MSG_SELL_NONE = "{0.mention}, you have no **{1}** to sell."
MSG_SELL_SUCCESS = "{0.mention}, you sold **{1} units** of **{2.name}** at `{5:,.2f} gil` per unit for a total of **💵 {3:,.2f} gil**. You now have **💵 {4:,.2f} gil**."
MSG_SHOW_HARVESTS_NONE = "{0.mention}, you have no harvested crops."
MSG_SHOW_HARVESTS = "{0.mention}, your current unsold harvests are:\n{1}"
MSG_SILO_PRICE_CHECK = "{0.mention}, your next **{2}** silos costs **💵 {1:,.2f} gil**. Each new silo upgrades your crop storage by 100."
MSG_SILO_BUY_SUCCESS = "{0.mention}, you have successfully bought **{2}** new silos! Your new balance is now **💵 {1:,.2f} gil**."
MSG_SHOW_STATS = (
    "**{0} Price History**\n"
    "***Y-axis*** ` Initial sell price `\n"
    "***X-axis*** ` (Date) | (Hour) `\n"
)
