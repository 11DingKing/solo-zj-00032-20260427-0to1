import React, { useEffect } from "react";
import {
  Layout as AntLayout,
  Menu,
  Button,
  Badge,
  Dropdown,
  Avatar,
  notification,
  Typography,
  List,
  Tag,
} from "antd";
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  TeamOutlined,
  AppstoreOutlined,
  HistoryOutlined,
  ImportOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuthStore, useAppStore } from "../store";
import api from "../utils/axios";
import { PendingFollowUp } from "../types";
import dayjs from "dayjs";

const { Header, Sider, Content } = AntLayout;
const { Text } = Typography;

const menuItems = [
  {
    key: "/dashboard",
    icon: <DashboardOutlined />,
    label: "数据看板",
  },
  {
    key: "/customers",
    icon: <TeamOutlined />,
    label: "客户管理",
  },
  {
    key: "/opportunities",
    icon: <AppstoreOutlined />,
    label: "商机管理",
  },
  {
    key: "/follow-ups",
    icon: <HistoryOutlined />,
    label: "跟进记录",
  },
  {
    key: "/import-export",
    icon: <ImportOutlined />,
    label: "数据导入导出",
  },
];

interface Props {
  children: React.ReactNode;
}

const Layout: React.FC<Props> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [notificationApi, contextHolder] = notification.useNotification();

  const collapsed = useAppStore((state) => state.collapsed);
  const toggleCollapsed = useAppStore((state) => state.toggleCollapsed);
  const pendingFollowUps = useAppStore((state) => state.pendingFollowUps);
  const setPendingFollowUps = useAppStore((state) => state.setPendingFollowUps);

  const user = useAuthStore((state) => ({
    name: state.name,
    email: state.email,
    role: state.role,
    company_name: state.company_name,
  }));
  const logout = useAuthStore((state) => state.logout);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    const fetchPendingFollowUps = async () => {
      try {
        const response = await api.get("/follow-ups/pending");
        const items: PendingFollowUp[] = response.data;
        setPendingFollowUps(items);

        if (items.length > 0) {
          notificationApi.open({
            message: "有待处理的跟进提醒",
            description: `您有 ${items.length} 条待处理的跟进记录`,
            icon: <BellOutlined style={{ color: "#faad14" }} />,
            placement: "topRight",
            duration: 5,
          });
        }
      } catch (error) {
        console.error("Failed to fetch pending follow-ups:", error);
      }
    };

    fetchPendingFollowUps();

    const interval = setInterval(fetchPendingFollowUps, 60000);
    return () => clearInterval(interval);
  }, [notificationApi, setPendingFollowUps]);

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const userMenuItems = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: `${user.name} (${user.role === "admin" ? "管理员" : user.role === "sales" ? "销售" : "只读"})`,
      disabled: true,
    },
    {
      key: "company",
      icon: <TeamOutlined />,
      label: user.company_name,
      disabled: true,
    },
    { type: "divider" as const },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "退出登录",
      onClick: handleLogout,
    },
  ];

  const getPendingMenuItems = () => {
    if (pendingFollowUps.length === 0) {
      return [
        {
          key: "empty",
          label: <Text type="secondary">暂无待处理的跟进</Text>,
        },
      ];
    }

    return [
      ...pendingFollowUps.slice(0, 5).map((item, index) => ({
        key: `item-${index}`,
        label: (
          <div style={{ maxWidth: 320 }}>
            <div style={{ fontWeight: "bold", marginBottom: 4 }}>
              {item.customer_name}
            </div>
            <div style={{ fontSize: 12, color: "#666", marginBottom: 4 }}>
              <Tag color="orange">
                {dayjs(item.next_follow_up_time).format("YYYY-MM-DD HH:mm")}
              </Tag>
            </div>
            <div
              style={{
                fontSize: 12,
                color: "#999",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {item.content}
            </div>
          </div>
        ),
      })),
      { type: "divider" as const },
      {
        key: "view-all",
        label: "查看全部跟进记录",
        onClick: () => navigate("/follow-ups"),
      },
    ];
  };

  const selectedKey = location.pathname.startsWith("/customers/")
    ? "/customers"
    : location.pathname;

  return (
    <>
      {contextHolder}
      <AntLayout style={{ minHeight: "100vh" }}>
        <Sider trigger={null} collapsible collapsed={collapsed}>
          <div className="logo">{collapsed ? "CRM" : "多租户 CRM"}</div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[selectedKey]}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Sider>
        <AntLayout>
          <Header
            style={{
              padding: "0 24px",
              background: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              boxShadow: "0 1px 4px rgba(0,21,41,0.08)",
            }}
          >
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={toggleCollapsed}
              style={{ fontSize: "16px", width: 64, height: 64 }}
            />

            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <Dropdown
                menu={{ items: getPendingMenuItems() }}
                placement="bottomRight"
                trigger={["click"]}
              >
                <Badge count={pendingFollowUps.length}>
                  <Button
                    type="text"
                    icon={<BellOutlined style={{ fontSize: 18 }} />}
                  >
                    提醒
                  </Button>
                </Badge>
              </Dropdown>

              <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                <div
                  style={{
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <Avatar icon={<UserOutlined />} />
                  <span>{user.name}</span>
                </div>
              </Dropdown>
            </div>
          </Header>
          <Content
            style={{
              margin: "24px",
              padding: 24,
              minHeight: 280,
              background: "#fff",
              borderRadius: 6,
            }}
          >
            {children}
          </Content>
        </AntLayout>
      </AntLayout>
    </>
  );
};

export default Layout;
