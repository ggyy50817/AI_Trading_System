class ReplayPosition:

    def __init__(self):
        self.position=None

    def has_position(self):
        return self.position is not None

    def open_position(self,symbol,side,price,candle):

        if side=="LONG":
            tp1=price*1.05
            tp2=price*1.10
            tp3=price*1.20
            sl=price*0.98
        else:
            tp1=price*0.95
            tp2=price*0.90
            tp3=price*0.80
            sl=price*1.02

        self.position={
            "symbol":symbol,
            "side":side,
            "entry_price":price,
            "entry_candle":candle,
            "tp1_done":False,
            "tp2_done":False,
            "tp3_done":False,
            "tp1":tp1,
            "tp2":tp2,
            "tp3":tp3,
            "stop_loss":sl
        }

        print(f"[OPEN] {symbol} {side} {price:.4f}")

    def update(self,high,low):

        if self.position is None:
            return None

        p=self.position

        if p["side"]=="LONG":

            if (not p["tp1_done"]) and high>=p["tp1"]:
                p["tp1_done"]=True
                return {"reason":"TP1","price":p["tp1"]}

            if (not p["tp2_done"]) and high>=p["tp2"]:
                p["tp2_done"]=True
                return {"reason":"TP2","price":p["tp2"]}

            if high>=p["tp3"]:
                r={"reason":"TP3","entry":p["entry_price"],"exit":p["tp3"]}
                self.position=None
                return r

            if low<=p["stop_loss"]:
                r={"reason":"SL","entry":p["entry_price"],"exit":p["stop_loss"]}
                self.position=None
                return r

        else:

            if (not p["tp1_done"]) and low<=p["tp1"]:
                p["tp1_done"]=True
                return {"reason":"TP1","price":p["tp1"]}

            if (not p["tp2_done"]) and low<=p["tp2"]:
                p["tp2_done"]=True
                return {"reason":"TP2","price":p["tp2"]}

            if low<=p["tp3"]:
                r={"reason":"TP3","entry":p["entry_price"],"exit":p["tp3"]}
                self.position=None
                return r

            if high>=p["stop_loss"]:
                r={"reason":"SL","entry":p["entry_price"],"exit":p["stop_loss"]}
                self.position=None
                return r

        return None
