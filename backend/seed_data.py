"""种子数据脚本 - 通过API创建测试数据"""
import httpx
import asyncio
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# 租户注册信息
TENANT = {
    "company_name": "测试科技",
    "admin_email": "admin@test.com",
    "admin_name": "管理员",
    "admin_password": "admin1234"
}

# 团队成员
USERS = [
    {"email": "sales1@test.com", "name": "张三(销售)", "role": "sales", "password": "sales1234"},
    {"email": "sales2@test.com", "name": "李四(销售)", "role": "sales", "password": "sales1234"},
    {"email": "viewer@test.com", "name": "王五(只读)", "role": "read_only", "password": "viewer1234"},
]

# 客户数据
CUSTOMERS = [
    {
        "company_name": "腾讯云",
        "industry": "互联网",
        "scale": "大型企业",
        "address": "深圳市南山区",
        "website": "cloud.tencent.com",
        "remark": "国内头部云服务商",
        "contacts": [
            {"name": "张伟", "position": "采购总监", "phone": "13800001111", "email": "zw@test.com", "is_primary": "true"},
            {"name": "李娜", "position": "技术经理", "phone": "13800001112", "email": "ln@test.com", "is_primary": "false"},
        ]
    },
    {
        "company_name": "瑞幸咖啡",
        "industry": "餐饮",
        "scale": "中型企业",
        "address": "厦门市思明区",
        "website": "luckin.com",
        "contacts": [
            {"name": "王强", "position": "IT负责人", "phone": "13800002222", "email": "wq@test.com", "is_primary": "true"},
        ]
    },
    {
        "company_name": "华为终端",
        "industry": "电子制造",
        "scale": "大型企业",
        "address": "深圳市龙岗区",
        "website": "huawei.com",
        "contacts": [
            {"name": "赵敏", "position": "供应链总监", "phone": "13800003333", "email": "zm@test.com", "is_primary": "true"},
        ]
    },
    {
        "company_name": "三只松鼠",
        "industry": "食品零售",
        "scale": "中型企业",
        "address": "芜湖市",
        "website": "3songshu.com",
        "contacts": [
            {"name": "刘洋", "position": "运营总监", "phone": "13800004444", "email": "ly@test.com", "is_primary": "true"},
        ]
    },
    {
        "company_name": "小鹏汽车",
        "industry": "汽车",
        "scale": "大型企业",
        "address": "广州市天河区",
        "website": "xiaopeng.com",
        "contacts": [
            {"name": "陈明", "position": "数字化总监", "phone": "13800005555", "email": "cm@test.com", "is_primary": "true"},
        ]
    },
]

# 商机数据 (customer_index, name, amount, stage, close_date)
OPPORTUNITIES = [
    (0, "腾讯云CRM系统采购", 500000, "proposal_quote", "2026-06-15"),
    (1, "瑞幸门店管理系统", 200000, "requirement_confirmation", "2026-07-01"),
    (2, "华为供应链平台", 800000, "initial_contact", "2026-08-30"),
    (3, "三只松鼠ERP升级", 350000, "won", "2026-04-10"),
    (0, "腾讯云数据中台", 300000, "negotiation", "2026-07-20"),
]

# 跟进记录 (customer_index, method, content, next_days_from_now)
FOLLOW_UPS = [
    (0, "visit", "拜访采购部张总，对CRM方案很感兴趣，要求出详细报价", 5),
    (0, "phone", "电话沟通报价细节，对方希望增加定制化模块", 10),
    (1, "wechat", "微信发送产品介绍文档，对方正在内部评估", 8),
    (2, "email", "发送公司资质和案例介绍邮件", 12),
    (3, "visit", "上门签约，项目正式启动", None),
    (4, "phone", "初次电话沟通，了解数字化需求", 7),
]


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        # 1. 注册租户
        print("=== 注册租户 ===")
        resp = await client.post("/api/register", json=TENANT)
        if resp.status_code == 200:
            print(f"  ✅ 租户 '{TENANT['company_name']}' 注册成功")
        elif resp.status_code == 400 and "already" in resp.text.lower():
            print(f"  ⚠️  租户已存在，跳过注册")
        else:
            print(f"  ❌ 注册失败: {resp.status_code} {resp.text}")
            return

        # 2. 管理员登录
        print("\n=== 管理员登录 ===")
        resp = await client.post("/api/login", data={
            "username": TENANT["admin_email"],
            "password": TENANT["admin_password"]
        })
        if resp.status_code != 200:
            print(f"  ❌ 登录失败: {resp.status_code} {resp.text}")
            return
        token_data = resp.json()
        admin_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        print(f"  ✅ 管理员登录成功")

        # 3. 创建团队成员
        print("\n=== 创建团队成员 ===")
        for u in USERS:
            resp = await client.post("/api/users", json=u, headers=headers)
            if resp.status_code == 200:
                print(f"  ✅ 用户 '{u['name']}' 创建成功")
            elif resp.status_code == 400:
                print(f"  ⚠️  用户 '{u['name']}' 已存在")
            else:
                print(f"  ❌ 创建失败: {resp.status_code} {resp.text}")

        # 4. 用sales1登录
        print("\n=== 销售登录 ===")
        resp = await client.post("/api/login", data={
            "username": "sales1@test.com",
            "password": "sales1234"
        })
        if resp.status_code != 200:
            print(f"  ❌ sales1登录失败: {resp.status_code} {resp.text}")
            return
        sales_token = resp.json()["access_token"]
        sales_headers = {"Authorization": f"Bearer {sales_token}"}
        print(f"  ✅ sales1 登录成功")

        # 5. 创建客户
        print("\n=== 创建客户 ===")
        customer_ids = []
        for c in CUSTOMERS:
            try:
                resp = await client.post("/api/customers", json=c, headers=sales_headers)
                if resp.status_code == 200:
                    cid = resp.json()["id"]
                    customer_ids.append(cid)
                    print(f"  ✅ 客户 '{c['company_name']}' 创建成功 (id={cid})")
                else:
                    customer_ids.append(None)
                    print(f"  ❌ 客户 '{c['company_name']}' 创建失败: {resp.status_code}")
            except Exception as e:
                customer_ids.append(None)
                print(f"  ❌ 客户 '{c['company_name']}' 请求异常: {e}")

        # 6. 创建商机
        print("\n=== 创建商机 ===")
        for ci, name, amount, stage, close_date in OPPORTUNITIES:
            if ci < len(customer_ids) and customer_ids[ci]:
                opp_data = {
                    "name": name,
                    "customer_id": customer_ids[ci],
                    "expected_amount": amount,
                    "expected_close_date": close_date,
                    "competitor_info": "竞品分析中"
                }
                resp = await client.post("/api/opportunities", json=opp_data, headers=sales_headers)
                if resp.status_code == 200:
                    oid = resp.json()["id"]
                    # 更新阶段
                    if stage != "initial_contact":
                        await client.put(f"/api/opportunities/{oid}", json={"stage": stage}, headers=sales_headers)
                    print(f"  ✅ 商机 '{name}' 创建成功 (阶段: {stage})")
                else:
                    print(f"  ❌ 商机 '{name}' 创建失败: {resp.status_code} {resp.text}")

        # 7. 创建跟进记录
        print("\n=== 创建跟进记录 ===")
        for ci, method, content, next_days in FOLLOW_UPS:
            if ci < len(customer_ids) and customer_ids[ci]:
                fu_data = {
                    "customer_id": customer_ids[ci],
                    "method": method,
                    "content": content,
                }
                if next_days is not None:
                    fu_data["next_follow_up_time"] = (datetime.now() + timedelta(days=next_days)).isoformat()
                resp = await client.post("/api/follow-ups", json=fu_data, headers=sales_headers)
                if resp.status_code == 200:
                    print(f"  ✅ 跟进记录创建成功: {content[:30]}...")
                else:
                    print(f"  ❌ 跟进记录创建失败: {resp.status_code} {resp.text}")

        # 8. 更新部分客户状态
        print("\n=== 更新客户状态 ===")
        status_updates = [
            (0, "opportunity", "腾讯云"),
            (1, "interested", "瑞幸咖啡"),
            (3, "closed", "三只松鼠"),
        ]
        for ci, new_status, name in status_updates:
            if ci < len(customer_ids) and customer_ids[ci]:
                try:
                    resp = await client.put(
                        f"/api/customers/{customer_ids[ci]}",
                        json={"status": new_status},
                        headers=sales_headers
                    )
                    if resp.status_code == 200:
                        print(f"  ✅ {name} 状态更新为 {new_status}")
                    else:
                        print(f"  ❌ {name} 状态更新失败: {resp.status_code}")
                except Exception as e:
                    print(f"  ❌ {name} 状态更新异常: {e}")

        print("\n=== 数据初始化完成 ===")
        print(f"\n登录信息:")
        print(f"  管理员: admin@test.com / admin1234")
        print(f"  销售1:  sales1@test.com / sales1234")
        print(f"  销售2:  sales2@test.com / sales1234")
        print(f"  只读:   viewer@test.com / viewer1234")


if __name__ == "__main__":
    asyncio.run(main())
