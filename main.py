from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from pydantic import BaseModel
from models import Stock
import yfinance

app = FastAPI()

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)


class StockRequest(BaseModel):
    symbol: str


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/")
def dashboard(request: Request, forward_pe= None, forward_yield= None, ma50= None, ma200= None, db: Session = Depends(get_db)):
    """
    Displays the stocks screener dashboard
    :return:
    """
    stocks = db.query(Stock)
    if forward_pe:
        stocks = stocks.filter(Stock.forward_pe < forward_pe)

    if forward_yield:
        stocks = stocks.filter(Stock.forward_yield > forward_yield)

    if ma50:
        stocks = stocks.filter(Stock.price > Stock.ma50)

    if ma200:
        stocks = stocks.filter(Stock.price > Stock.ma200)

    return templates.TemplateResponse("dashboard.html", {
      "request": request,
      "stocks": stocks,
      "forward_yield": forward_yield,
      "forward_pe": forward_pe,
      "ma50": ma50,
      "ma200": ma200
    })


def fetch_stock_data(id: int):
    db = SessionLocal()
    stock = db.query(Stock).filter(Stock.id == id).first()

    yahoo_data = yfinance.Ticker(stock.symbol)

    stock.ma200 = float(yahoo_data.info['twoHundredDayAverage'])
    stock.ma50 = float(yahoo_data.info['fiftyDayAverage'])
    stock.price = float(yahoo_data.info['previousClose'])
    stock.forward_pe = float(yahoo_data.info['forwardPE'])
    stock.forward_eps = float(yahoo_data.info['forwardEps'])

    if yahoo_data.info['dividendYield'] is not None:
        stock.dividend_yield = float(yahoo_data.info['dividendYield'] * 100)

    db.add(stock)
    db.commit()


@app.post("/stock")
async def create_stock(stock_request: StockRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Creates a stock and stores it in the database
    :return:
    """
    stock = Stock()
    stock.symbol = stock_request.symbol

    db.add(stock)
    db.commit()

    background_tasks.add_task(
        fetch_stock_data, stock.id
    )

    return {"code": "success", "message": "stock created"}
