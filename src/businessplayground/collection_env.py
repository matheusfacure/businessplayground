import pandas as pd
import datetime
from datetime import timedelta
from toolz import curry

import numpy as np
from matplotlib import pyplot as plt
import uuid


@curry
def financial_educ_fn(df: pd.DataFrame, age_col: str, fin_ed_col: str):
    n = df.shape[0]
    financial_educ = (
        (np.random.beta(10, 20, n) +
         np.random.beta(df[age_col]/(10 * 365), 2)) * 50 # higher than 50 after ~30 year
    )
    return df.assign(**{fin_ed_col: financial_educ.astype(int)})


@curry
def debt_fn(df: pd.DataFrame, fin_ed_col: str, debt_col: str):
    n = df.shape[0]
    debt = np.random.normal(5000/df[fin_ed_col], 700, n)
    debt = np.maximum(debt, 10)
    return df.assign(**{debt_col: debt})


@curry
def discount_fn(df: pd.DataFrame, discount_col: str, debt_col: str, max_discount: float = 0.5):
    n = df.shape[0]
    discount = np.random.binomial(1,0.5,n)
    discount = discount * np.random.beta(0.9, 4, n)
    discount = np.minimum(discount, max_discount)
    return df.assign(**{discount_col: discount})


@curry
def update_interest_fn(df: pd.DataFrame, intr_col: str, debt_col: str, days_late_col: int, daily_intr: float=0.004):
    intr = np.where(df[days_late_col] < 100, df[debt_col] * daily_intr, 0) # interest only untill 100 days late
    return df.assign(**{intr_col: df[intr_col] + intr})


@curry
def update_fin_ed(df: pd.DataFrame, fin_ed_col: str, lr_rate: float):
    n = df.shape[0]
    financial_educ = (
        ((df[fin_ed_col] * (1-lr_rate)) +
         (np.random.beta(10, 1, n) * 100 * lr_rate))
    )
    return df.assign(**{fin_ed_col: financial_educ})


@curry
def payment_fn(df: pd.DataFrame, payment_col: str, initil_debt_col: str, debt_col: str,
               intr_col: str, fin_ed_col: str):
    
    n = df.shape[0]
    payment = np.random.normal((50 + 
                                .05 * df[initil_debt_col] -
                                2.0 * df[intr_col] +
                                10 * (df[fin_ed_col] - 50)),
                               50)
    payment = np.clip(payment, 0, df[debt_col] + df[intr_col])
    return df.assign(**{payment_col: payment})


@curry
def update_debt(df: pd.DataFrame, debt_col: str, payment_col: str, intr_col: str):
    n = df.shape[0]
    debt = df[debt_col] + df[intr_col] - df[payment_col]
    return df.assign(**{debt_col: debt})



class envoriment(object):
    def __init__(self,):
        self.date = datetime.datetime(2016, 1, 1)
        self.history = pd.DataFrame({
            "id": [str(uuid.uuid1())],
            "date": [self.date],
            "initial_debt": [1000.],
            "debt": [1000.],
            "days_late": [1],
            "payment": [0.],
            "age":[20 * 365],
            "discount": [0.],
            "interest": [0.],
            "action":[np.nan],
            
            # hidden variables
            "financial_educ": [45.],
        })
        
    def get_new_customers(self, date, n):
        return (pd.DataFrame({
            "id": [str(uuid.uuid1()) for _ in range(n)],
            "age": ((np.random.gamma(2, 10, n) + 18) * 365).astype(int),
        })
                .assign(date = date,
                        days_late = 1,
                        payment = 0.,
                        discount = 0.,
                        interest = 0.0,
                        action = np.nan)
                .pipe(financial_educ_fn(age_col="age", fin_ed_col="financial_educ"))
                .pipe(debt_fn(fin_ed_col="financial_educ", debt_col="initial_debt"))
                .assign(debt=lambda d: d["initial_debt"])
               )
    
    def update(self, old: pd.DataFrame, date):
        return (old
                .assign(date = date)
                .assign(age = lambda d: d["age"] + 1)
                .assign(days_late = lambda d: d["days_late"] + 1)
                .pipe(update_interest_fn(intr_col="interest", debt_col="debt", days_late_col="days_late"))
                .pipe(update_fin_ed(fin_ed_col="financial_educ", lr_rate=0.01))
                .pipe(discount_fn(discount_col="discount", debt_col="debt"))
                .pipe(payment_fn(payment_col="payment",
                                 intr_col="interest",
                                 initil_debt_col="initial_debt",
                                 debt_col = "debt",
                                 fin_ed_col="financial_educ"))
                .pipe(update_debt(payment_col="payment", intr_col="interest", debt_col="debt",))
               )
        
    
    def next_day(self,):
        
        today = self.date + timedelta(days=1)
        
        # new customers
        n_new_cust = np.random.poisson(5)
        new_customers = self.get_new_customers(today, n_new_cust)
        
        # update old customers
        old_cust_yesterday = (self
                              .history[self.history["date"] == self.date]
                              .query("debt>=payment")
                             )
        
        old_cust_today = self.update(old_cust_yesterday, today)
        
        self.date = today
        self.history = pd.concat([self.history, old_cust_today, new_customers], sort=False).reset_index(drop=True)
    
