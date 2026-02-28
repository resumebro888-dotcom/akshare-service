"""
A股超短线交易智能体 - AKShare 数据中间服务 v3
所有接口名称已通过官方文档验证
"""

from flask import Flask, jsonify, request
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta, date, time as dt_time
import traceback
import json
import decimal

app = Flask(__name__)


# ============================================================
# 核心工具函数：解决所有序列化问题
# ============================================================
class SafeEncoder(json.JSONEncoder):
    """处理所有 Python 特殊类型的 JSON 编码器"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dt_time):
            return obj.strftime("%H:%M:%S")
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, pd.Timedelta):
            return str(obj)
        if hasattr(obj, 'item'):  # numpy int/float
            return obj.item()
        return str(obj)


app.json_encoder = SafeEncoder


def df_to_list(df, max_rows=None):
    """将 DataFrame 安全转为可 JSON 序列化的 list"""
    if df is None or df.empty:
        return []
    if max_rows:
        df = df.head(max_rows)

    records = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if val is None or (isinstance(val, float) and pd.isna(val)):
                record[col] = None
            elif isinstance(val, (datetime, date, pd.Timestamp)):
                record[col] = str(val)
            elif isinstance(val, dt_time):
                record[col] = val.strftime("%H:%M:%S")
            elif isinstance(val, decimal.Decimal):
                record[col] = float(val)
            elif hasattr(val, 'item'):
                record[col] = val.item()
            else:
                record[col] = val
        records.append(record)
    return records


def make_response(data, **kwargs):
    """统一构造响应"""
    result = {"data": data, "count": len(data)}
    result.update(kwargs)
    return json.loads(json.dumps(result, cls=SafeEncoder, ensure_ascii=False))


# ============================================================
# 首页
# ============================================================
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "version": "v3",
        "akshare_version": ak.__version__,
        "endpoints": [
            "GET /api/limit_up?date=20250228",
            "GET /api/limit_up_yesterday",
            "GET /api/sector_fund_flow?indicator=今日",
            "GET /api/stock_fund_flow?indicator=今日",
            "GET /api/stock_fund_flow_single?stock=000001",
            "GET /api/sector_spot",
            "GET /api/sector_stocks?symbol=光伏",
            "GET /api/stock_spot?codes=000001,600000",
            "GET /api/index_spot",
            "GET /api/news",
            "GET /api/minute?symbol=000001&period=1",
            "GET /api/market_sentiment",
            "GET /health",
        ]
    })


# ============================================================
# 1. 涨停板数据
# 接口: ak.stock_zt_pool_em(date="20250228")
# ============================================================
@app.route("/api/limit_up", methods=["GET"])
def limit_up():
    try:
        date = request.args.get("date", datetime.now().strftime("%Y%m%d"))
        df = ak.stock_zt_pool_em(date=date)
        data = df_to_list(df)
        return jsonify(make_response(data, date=date))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 2. 昨日涨停股池
# 接口: ak.stock_zt_pool_previous_em()
# ============================================================
@app.route("/api/limit_up_yesterday", methods=["GET"])
def limit_up_yesterday():
    try:
        df = ak.stock_zt_pool_previous_em()
        data = df_to_list(df)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 3. 板块资金流排名
# 接口: ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="概念资金流")
# ============================================================
@app.route("/api/sector_fund_flow", methods=["GET"])
def sector_fund_flow():
    try:
        indicator = request.args.get("indicator", "今日")
        sector_type = request.args.get("sector_type", "概念资金流")
        df = ak.stock_sector_fund_flow_rank(indicator=indicator, sector_type=sector_type)
        data = df_to_list(df)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 4. 个股资金流排名
# 接口: ak.stock_individual_fund_flow_rank(indicator="今日")
# ============================================================
@app.route("/api/stock_fund_flow", methods=["GET"])
def stock_fund_flow():
    try:
        indicator = request.args.get("indicator", "今日")
        df = ak.stock_individual_fund_flow_rank(indicator=indicator)
        data = df_to_list(df)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 5. 单只个股资金流向
# 接口: ak.stock_individual_fund_flow(stock="000001", market="sz")
# ============================================================
@app.route("/api/stock_fund_flow_single", methods=["GET"])
def stock_fund_flow_single():
    try:
        stock = request.args.get("stock", "")
        if not stock:
            return jsonify({"error": "请提供 stock 参数（如 000001）"}), 400
        market = request.args.get("market", "")
        if not market:
            market = "sh" if stock.startswith("6") else "sz"
        df = ak.stock_individual_fund_flow(stock=stock, market=market)
        data = df_to_list(df, max_rows=5)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 6. 板块实时行情（概念板块排行）
# 接口: ak.stock_board_concept_name_em()
# ============================================================
@app.route("/api/sector_spot", methods=["GET"])
def sector_spot():
    try:
        df = ak.stock_board_concept_name_em()
        data = df_to_list(df)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 7. 板块成分股
# 接口: ak.stock_board_concept_cons_em(symbol="光伏")
# ============================================================
@app.route("/api/sector_stocks", methods=["GET"])
def sector_stocks():
    try:
        symbol = request.args.get("symbol", "")
        if not symbol:
            return jsonify({"error": "请提供 symbol 参数（板块名称，如 光伏）"}), 400
        df = ak.stock_board_concept_cons_em(symbol=symbol)
        data = df_to_list(df)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 8. 个股实时行情
# 接口: ak.stock_zh_a_spot_em()
# ============================================================
@app.route("/api/stock_spot", methods=["GET"])
def stock_spot():
    try:
        df = ak.stock_zh_a_spot_em()
        codes = request.args.get("codes", "")
        if codes:
            code_list = [c.strip() for c in codes.split(",")]
            col_name = "代码" if "代码" in df.columns else df.columns[1]
            df = df[df[col_name].isin(code_list)]
        data = df_to_list(df)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 9. 大盘指数实时行情
# 接口: ak.stock_zh_index_spot_sina()
# 注意: stock_zh_index_spot_em 需要 symbol 参数，不如 sina 版方便
# ============================================================
@app.route("/api/index_spot", methods=["GET"])
def index_spot():
    try:
        df = ak.stock_zh_index_spot_sina()
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        major_codes = ["sh000001", "sz399001", "sh000300", "sz399006"]
        col_name = "代码" if "代码" in df.columns else df.columns[0]
        df_major = df[df[col_name].isin(major_codes)]
        data = df_to_list(df_major)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 10. 财联社快讯
# 接口: ak.stock_telegraph_cls(symbol="全部")
# ============================================================
@app.route("/api/news", methods=["GET"])
def news():
    try:
        df = ak.stock_telegraph_cls(symbol="全部")
        data = df_to_list(df, max_rows=50)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 11. 分钟级行情
# 接口: ak.stock_zh_a_hist_min_em(symbol="000001", period="1", adjust="")
# ============================================================
@app.route("/api/minute", methods=["GET"])
def minute_data():
    try:
        symbol = request.args.get("symbol", "")
        period = request.args.get("period", "1")
        if not symbol:
            return jsonify({"error": "请提供 symbol 参数（如 000001）"}), 400
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period=period, adjust="")
        data = df_to_list(df, max_rows=60)
        return jsonify(make_response(data))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 12. 市场情绪统计
# ============================================================
@app.route("/api/market_sentiment", methods=["GET"])
def market_sentiment():
    try:
        date = request.args.get("date", datetime.now().strftime("%Y%m%d"))
        results = {}

        try:
            zt = ak.stock_zt_pool_em(date=date)
            results["涨停数"] = len(zt) if zt is not None and not zt.empty else 0
        except Exception:
            results["涨停数"] = "获取失败"

        try:
            dt = ak.stock_zt_pool_dtgc_em(date=date)
            results["跌停数"] = len(dt) if dt is not None and not dt.empty else 0
        except Exception:
            results["跌停数"] = "获取失败"

        try:
            zb = ak.stock_zt_pool_zbgc_em(date=date)
            results["炸板数"] = len(zb) if zb is not None and not zb.empty else 0
        except Exception:
            results["炸板数"] = "获取失败"

        return jsonify({"data": results, "date": date})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# 健康检查
# ============================================================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "akshare_version": ak.__version__})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
