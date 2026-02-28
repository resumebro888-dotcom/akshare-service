"""
A股超短线交易智能体 - AKShare 数据中间服务
部署在 Railway 上，供 Coze 工作流调用
"""

from flask import Flask, jsonify, request
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "service": "A股超短线交易数据服务",
        "endpoints": [
            "/api/limit_up - 涨停板数据",
            "/api/sector_fund_flow - 板块资金流排名",
            "/api/stock_fund_flow - 个股资金流",
            "/api/sector_spot - 板块实时行情",
            "/api/stock_spot - 个股实时行情",
            "/api/index_spot - 大盘指数行情",
            "/api/news - 财联社快讯",
            "/api/minute - 分钟级行情",
        ]
    })


# ============================================================
# 1. 涨停板数据
# ============================================================
@app.route("/api/limit_up", methods=["GET"])
def limit_up():
    """获取涨停股池数据"""
    try:
        date = request.args.get("date", "")
        if date:
            df = ak.stock_zt_pool_em(date=date)
        else:
            df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))

        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据，可能非交易日"})

        result = df.to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 2. 昨日涨停股池
# ============================================================
@app.route("/api/limit_up_yesterday", methods=["GET"])
def limit_up_yesterday():
    """获取昨日涨停股池（用于判断连板和板块持续性）"""
    try:
        df = ak.stock_zt_pool_previous_em()
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        result = df.to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 3. 板块资金流排名
# ============================================================
@app.route("/api/sector_fund_flow", methods=["GET"])
def sector_fund_flow():
    """获取板块资金流排名（概念板块）"""
    try:
        indicator = request.args.get("indicator", "今日")
        sector_type = request.args.get("sector_type", "概念资金流")
        df = ak.stock_sector_fund_flow_rank(indicator=indicator, sector_type=sector_type)
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        result = df.to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 4. 个股资金流排名
# ============================================================
@app.route("/api/stock_fund_flow", methods=["GET"])
def stock_fund_flow():
    """获取个股资金流排名"""
    try:
        indicator = request.args.get("indicator", "今日")
        df = ak.stock_individual_fund_flow_rank(indicator=indicator)
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        result = df.to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 5. 单只个股资金流向（按股票代码查询）
# ============================================================
@app.route("/api/stock_fund_flow_single", methods=["GET"])
def stock_fund_flow_single():
    """获取单只股票的资金流向"""
    try:
        stock = request.args.get("stock", "")
        market = request.args.get("market", "")
        if not stock:
            return jsonify({"error": "请提供 stock 参数（如 000001）"}), 400

        # 自动判断市场
        if not market:
            if stock.startswith("6"):
                market = "sh"
            else:
                market = "sz"

        df = ak.stock_individual_fund_flow(stock=stock, market=market)
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        # 只返回最近5天
        result = df.head(5).to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 6. 板块实时行情（概念板块排行）
# ============================================================
@app.route("/api/sector_spot", methods=["GET"])
def sector_spot():
    """获取概念板块实时行情排行"""
    try:
        df = ak.stock_board_concept_name_em()
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        result = df.to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 7. 板块成分股
# ============================================================
@app.route("/api/sector_stocks", methods=["GET"])
def sector_stocks():
    """获取指定概念板块的成分股"""
    try:
        symbol = request.args.get("symbol", "")
        if not symbol:
            return jsonify({"error": "请提供 symbol 参数（板块名称）"}), 400

        df = ak.stock_board_concept_cons_em(symbol=symbol)
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        result = df.to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 8. 个股实时行情（全市场）
# ============================================================
@app.route("/api/stock_spot", methods=["GET"])
def stock_spot():
    """获取沪深京A股实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})

        # 可选：按股票代码列表过滤
        codes = request.args.get("codes", "")
        if codes:
            code_list = [c.strip() for c in codes.split(",")]
            df = df[df["代码"].isin(code_list)]

        result = df.to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 9. 大盘指数实时行情
# ============================================================
@app.route("/api/index_spot", methods=["GET"])
def index_spot():
    """获取主要指数实时行情"""
    try:
        df = ak.stock_zh_index_spot_sina()
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})

        # 筛选主要指数：上证指数、深证成指、沪深300、创业板指
        major_codes = ["sh000001", "sz399001", "sh000300", "sz399006"]
        df_major = df[df["代码"].isin(major_codes)]

        result = df_major.to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 10. 财联社快讯
# ============================================================
@app.route("/api/news", methods=["GET"])
def news():
    """获取财联社电报快讯"""
    try:
        df = ak.stock_telegraph_cls()
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        # 返回最新50条
        result = df.head(50).to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 11. 分钟级行情
# ============================================================
@app.route("/api/minute", methods=["GET"])
def minute_data():
    """获取个股分钟级行情数据"""
    try:
        symbol = request.args.get("symbol", "")
        period = request.args.get("period", "1")  # 1, 5, 15, 30, 60
        if not symbol:
            return jsonify({"error": "请提供 symbol 参数（如 000001）"}), 400

        df = ak.stock_zh_a_minute(symbol=f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}", period=period)
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        # 返回最近60条
        result = df.tail(60).to_dict(orient="records")
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 12. 赚钱效应分析（涨停、跌停、炸板统计）
# ============================================================
@app.route("/api/market_sentiment", methods=["GET"])
def market_sentiment():
    """获取市场赚钱效应分析数据"""
    try:
        results = {}

        # 涨停数量
        try:
            zt = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
            results["涨停数"] = len(zt) if zt is not None else 0
        except:
            results["涨停数"] = "获取失败"

        # 跌停数量
        try:
            dt = ak.stock_zt_pool_dtgc_em(date=datetime.now().strftime("%Y%m%d"))
            results["跌停数"] = len(dt) if dt is not None else 0
        except:
            results["跌停数"] = "获取失败"

        # 炸板数量
        try:
            zb = ak.stock_zt_pool_zbgc_em(date=datetime.now().strftime("%Y%m%d"))
            results["炸板数"] = len(zb) if zb is not None else 0
        except:
            results["炸板数"] = "获取失败"

        return jsonify({"data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
