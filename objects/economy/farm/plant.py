from datetime import datetime, timedelta
from random import randint
import logging

from sqlalchemy import Table, Column, Boolean, Integer, BigInteger, String, MetaData, DateTime
from sqlalchemy.orm import relationship

from config import *
from objects.base import Base
from objects.economy.farm.plot import Plot
from objects.economy.farm.farm import Farm
from objects.economy.farm.pricelog import PriceLog
import utils.graphing as graphutils

import matplotlib.pyplot as plt

class Plant(Base):
    __tablename__ = 'farm_plants'

    id = Column(Integer, primary_key=True)

    name = Column(String(64), unique=True) # Turnip
    tag = Column(String(4), unique=True) # TRNP
    buy_price = Column(BigInteger) # 50000
    base_harvest = Column(Integer) # 10

    base_sell_price = Column(BigInteger) # 20000
    current_sell_price = Column(BigInteger) # Set dynamically
    randomness_factor = Column(BigInteger) # / 10000

    growing_seconds = Column(BigInteger)

    current_demand = Column(BigInteger, default=1)
    base_demand = Column(BigInteger, default=1)
    current_demand_factor = Column(BigInteger, default=40000)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    price_logs = relationship("PriceLog", back_populates="plant")

    @staticmethod
    def get_plants(session):
        all_plants = session.query(Plant).order_by(Plant.buy_price).all()
        return all_plants

    @staticmethod
    def get_plant(session, name):
        plant = session.query(Plant).filter(Plant.name.ilike(name)).first()
        if plant is None:
            plant = session.query(Plant).filter(Plant.tag.ilike(name)).first()
        return plant
    
    def get_buy_price(self):
        return self.buy_price / 10000
    
    def get_sell_price(self, raw=False):
        cd, bd = self.current_demand, self.base_demand
        df = self.current_demand_factor / 10000
        sell_price = (self.current_sell_price / 2) * df**((cd**2)/(bd**2))
        sell_price = int(sell_price)
        if raw:
            return sell_price
        return sell_price / 10000

    def get_highest_sell_price(self):
        sorted_logs = sorted(self.price_logs, key=lambda x:x.price, reverse=True)
        return sorted_logs[0]

    def decrement_demand(self, session, amount):
        self.current_demand = max(self.current_demand - amount, 0)
        session.add(self)
        session.commit()

    def generate_prices_graph(self, session):
        time_now = datetime.now()
        plant_stats_24h = self.price_logs[:24]
        
        # x_points = [ 
        #     _stat.refreshed_at.strftime("%H:%M") for _stat in plant_stats_24h
        # ]
        x_points = [ 
            _stat.refreshed_at.strftime("%H:%M") for _stat in plant_stats_24h
        ]
        y_points = [ 
            int(_stat.price) / 10000 for _stat in plant_stats_24h
        ]
        
        graph_file = PLANT_PRICE_GRAPH_DIRECTORY + "{}.png".format(self.tag.upper())
        
        title = "Prices"

        graphutils.plot_graph(x_points, y_points, title, graph_file)

    def randomize_price(self, session, commit_on_execution=True):
        _farms = Farm.get_farms_count(session)
        _plots = Plot.get_plots_count(session)

        # Demand factor calculation
        df = self.current_demand_factor
        bd, cd = self.base_demand, self.current_demand
        market_change_percent = (cd - (bd*MARKET_TOLERANCE)) / bd

        df_non_raw = df / 10000
        if market_change_percent < 0:
            # Reset the demand factor if market is saturated
            new_demand_factor = 4 * (df_non_raw ** (MARKET_TOLERANCE + market_change_percent))
            new_demand_factor *= 10000
        else:
            new_demand_factor = df * (4 ** market_change_percent)
        self.current_demand_factor = int(new_demand_factor)
        
        # Demand calculation
        growth_rate = max(3600 / self.growing_seconds, 1)
        _demand = self.base_harvest * growth_rate * (_plots) * (4 / (new_demand_factor / 10000))
        
        logging.info("Recalculated {}: {} => {}".format(self.tag, _demand, new_demand_factor / 10000))
        
        self.base_demand = max(int(_demand / DEMAND_DIVISOR), 1)
        self.current_demand = max(int(_demand / DEMAND_DIVISOR), 1)
        
        # Price calculation
        _r = self.randomness_factor
        rand_factor = randint(10000-_r, 10000+_r) / 10000
        self.current_sell_price = int(self.base_sell_price*rand_factor)

        session.add(self)
        PriceLog.log_price(self, session, commit_on_execution=commit_on_execution)
        
        if commit_on_execution:
            session.commit()

        self.generate_prices_graph(session)

    def set_base_price(self, session, price, raw=False):
        if not raw:
            price *= 10000
        self.base_sell_price = price
        session.add(self)
        session.commit()
