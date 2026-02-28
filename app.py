"""
A股超短线交易智能体 - AKShare 数据中间服务 v2
修复接口名称，适配 AKShare 1.14+
"""

from flask import Flask, jsonify, request
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import traceback

app = Flask(__name__)


def safe_to_dict(df, max_rows=None):
    """安全地将 DataFrame 转为 dict，处理 NaN 和日期"""
    if df is None or df.empty:
        return []
    if max_rows:
        df = df.head(max_rows)
    # 将 NaN 替换为 None，日期转字符串
    df = df.where(pd.notnull(df), None)
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)
    return df.to_dict(orient="records")


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "version": "v2",
        "service": "A股超短线交易数据服务",
        "endpoints": [
            "/api/limit_up - 涨停板数据",
            "/api/limit_up_yesterday - 昨日涨停股池",
            "/api/sector_fund_flow - 板块资金流排名",
            "/api/stock_fund_flow - 个股资金流排名",
            "/api/stock_fund_flow_single - 单只股票资金流",
            "/api/sector_spot - 板块实时行情",
            "/api/sector_stocks - 板块成分股",
            "/api/stock_spot - 个股实时行情",
            "/api/index_spot - 大盘指数行情",
            "/api/news - 财联社快讯",
            "/api/minute - 分钟级行情",
            "/api/market_sentiment - 市场情绪统计",
        ]
    })


# ============================================================
# 1. 涨停板数据
# ============================================================
@app.route("/api/limit_up", methods=["GET"])
def limit_up():
    """获取涨停股池数据"""
    try:
        date = request.args.get("date", datetime.now().strftime("%Y%m%d"))
        df = ak.stock_zt_pool_em(date=date)
        result = safe_to_dict(df)
        return jsonify({"data": result, "count": len(result), "date": date})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 2. 昨日涨停股池
# ============================================================
@app.route("/api/limit_up_yesterday", methods=["GET"])
def limit_up_yesterday():
    """获取昨日涨停股池"""
    try:
        df = ak.stock_zt_pool_previous_em()
        result = safe_to_dict(df)
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 3. 板块资金流排名
# ============================================================
@app.route("/api/sector_fund_flow", methods=["GET"])
def sector_fund_flow():
    """获取板块资金流排名"""
    try:
        indicator = request.args.get("indicator", "今日")
        sector_type = request.args.get("sector_type", "概念资金流")
        df = ak.stock_sector_fund_flow_rank(indicator=indicator, sector_type=sector_type)
        result = safe_to_dict(df)
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 4. 个股资金流排名
# ============================================================
@app.route("/api/stock_fund_flow", methods=["GET"])
def stock_fund_flow():
    """获取个股资金流排名"""
    try:
        indicator = request.args.get("indicator", "今日")
        df = ak.stock_individual_fund_flow_rank(indicator=indicator)
        result = safe_to_dict(df)
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 5. 单只个股资金流向
# ============================================================
@app.route("/api/stock_fund_flow_single", methods=["GET"])
def stock_fund_flow_single():
    """获取单只股票的资金流向"""
    try:
        stock = request.args.get("stock", "")
        market = request.args.get("market", "")
        if not stock:
            return jsonify({"error": "请提供 stock 参数（如 000001）"}), 400
        if not market:
            market = "sh" if stock.startswith("6") else "sz"
        df = ak.stock_individual_fund_flow(stock=stock, market=market)
        result = safe_to_dict(df, max_rows=5)
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 6. 板块实时行情
# ============================================================
@app.route("/api/sector_spot", methods=["GET"])
def sector_spot():
    """获取概念板块实时行情排行"""
    try:
        df = ak.stock_board_concept_name_em()
        result = safe_to_dict(df)
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


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
        result = safe_to_dict(df)
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 8. 个股实时行情
# ============================================================
@app.route("/api/stock_spot", methods=["GET"])
def stock_spot():
    """获取沪深京A股实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        codes = request.args.get("codes", "")
        if codes:
            code_list = [c.strip() for c in codes.split(",")]
            df = df[df["代码"].isin(code_list)]
        result = safe_to_dict(df)
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 9. 大盘指数实时行情
# ============================================================
@app.route("/api/index_spot", methods=["GET"])
def index_spot():
    """获取主要指数实时行情"""
    try:
        # 使用东方财富的全球指数接口，更稳定
        df = ak.stock_zh_index_spot_em()
        if df is None or df.empty:
            return jsonify({"data": [], "msg": "无数据"})
        # 筛选主要A股指数
        keywords = ["上证指数", "深证成指", "沪深300", "创业板指"]
        df_major = df[df["名称"].isin(keywords)]
        if df_major.empty:
            # 如果精确匹配为空，尝试模糊匹配
            mask = df["名称"].str.contains("|".join(keywords), na=False)
            df_major = df[mask]
        result = safe_to_dict(df_major)
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        # 备用方案：尝试新浪接口
        try:
            df = ak.stock_zh_index_spot_sina()
            major_codes = ["sh000001", "sz399001", "sh000300", "sz399006"]
            df_major = df[df["代码"].isin(major_codes)]
            result = safe_to_dict(df_major)
            return jsonify({"data": result, "count": len(result), "source": "sina"})
        except Exception as e2:
            return jsonify({"error": str(e), "backup_error": str(e2), "detail": traceback.format_exc()}), 500


# ============================================================
# 10. 财联社快讯
# ============================================================
@app.route("/api/news", methods=["GET"])
def news():
    """获取财联社电报快讯"""
    try:
        # 正确的接口名和参数
        df = ak.stock_telegraph_cls(symbol="全部")
        result = safe_to_dict(df, max_rows=50)
        return jsonify({"data": result, "count": len(result)})
    except AttributeError:
        # 如果接口名变了，尝试备用名
        try:
            df = ak.stock_info_global_cls()
            result = safe_to_dict(df, max_rows=50)
            return jsonify({"data": result, "count": len(result), "source": "stock_info_global_cls"})
        except Exception as e2:
            return jsonify({"error": f"两个接口都失败: {str(e2)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 11. 分钟级行情
# ============================================================
@app.route("/api/minute", methods=["GET"])
def minute_data():
    """获取个股分钟级行情数据"""
    try:
        symbol = request.args.get("symbol", "")
        period = request.args.get("period", "1")
        if not symbol:
            return jsonify({"error": "请提供 symbol 参数（如 000001）"}), 400

        # 使用东方财富分钟数据接口
        df = ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            period=period,
            adjust=""
        )
        result = safe_to_dict(df, max_rows=60)
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 12. 市场情绪统计
# ============================================================
@app.route("/api/market_sentiment", methods=["GET"])
def market_sentiment():
    """获取市场赚钱效应分析数据"""
    try:
        date = request.args.get("date", datetime.now().strftime("%Y%m%d"))
        results = {}

        try:
            zt = ak.stock_zt_pool_em(date=date)
            results["涨停数"] = len(zt) if zt is not None and not zt.empty else 0
        except:
            results["涨停数"] = "获取失败"

        try:
            dt = ak.stock_zt_pool_dtgc_em(date=date)
            results["跌停数"] = len(dt) if dt is not None and not dt.empty else 0
        except:
            results["跌停数"] = "获取失败"

        try:
            zb = ak.stock_zt_pool_zbgc_em(date=date)
            results["炸板数"] = len(zb) if zb is not None and not zb.empty else 0
        except:
            results["炸板数"] = "获取失败"

        return jsonify({"data": results, "date": date})
    except Exception as e:
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500


# ============================================================
# 健康检查
# ============================================================
@app.route("/health", methods=["GET"])
def health():
    """健康检查接口"""
    return jsonify({"status": "ok", "akshare_version": ak.__version__})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
