import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Button, Spin, message, Table } from 'antd';
import {
  TeamOutlined,
  DollarOutlined,
  SyncOutlined,
  RiseOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  ResponsiveContainer,
  FunnelChart,
  Funnel,
  LabelList,
} from 'recharts';
import api from '../utils/axios';
import { DashboardStats, SalesRankItem, IndustryDistribution, FunnelItem, MonthlyTrendItem } from '../types';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const stageLabels: Record<string, string> = {
  'initial_contact': '初步接触',
  'requirement_confirmation': '需求确认',
  'proposal_quote': '方案报价',
  'negotiation': '商务谈判',
  'won': '赢单',
  'lost': '输单',
};

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  const fetchStats = async (refresh = false) => {
    setLoading(true);
    try {
      const params = refresh ? { refresh: true } : {};
      const response = await api.get('/dashboard', { params });
      setStats(response.data);
      if (refresh) {
        message.success('数据已刷新');
      }
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const salesRankColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '销售',
      dataIndex: 'user_name',
      key: 'user_name',
    },
    {
      title: '成单数',
      dataIndex: 'won_count',
      key: 'won_count',
    },
    {
      title: '成交金额',
      dataIndex: 'won_amount',
      key: 'won_amount',
      render: (value: number) => `¥${value.toLocaleString()}`,
    },
  ];

  if (loading && !stats) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  const funnelData = stats?.opportunity_funnel.map((item) => ({
    ...item,
    stage: stageLabels[item.stage] || item.stage,
  })) || [];

  const industryData = stats?.industry_distribution.map((item, index) => ({
    ...item,
    fill: COLORS[index % COLORS.length],
  })) || [];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>数据看板</h2>
        <Button
          icon={<SyncOutlined spin={loading} />}
          onClick={() => fetchStats(true)}
        >
          刷新数据
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="本月新增客户"
              value={stats?.monthly_new_customers || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="本月新增商机金额"
              value={stats?.monthly_new_opportunity_amount || 0}
              prefix={<DollarOutlined />}
              suffix="元"
              valueStyle={{ color: '#52c41a' }}
              formatter={(value) => `${value.toLocaleString()}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="活跃商机数"
              value={stats?.opportunity_funnel.filter(f => !['won', 'lost'].includes(f.stage)).reduce((sum, f) => sum + f.count, 0) || 0}
              prefix={<AppstoreOutlined as any />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="销售人数"
              value={stats?.sales_rank.length || 0}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="商机漏斗图">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={funnelData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#1890ff" name="商机数量" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="客户行业分布">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={industryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ industry, count, percent }) => `${industry}: ${count} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                  nameKey="industry"
                >
                  {industryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="近12个月成交金额趋势">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={stats?.monthly_trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value: number) => `¥${value.toLocaleString()}`} />
                <Legend />
                <Line type="monotone" dataKey="amount" stroke="#1890ff" name="成交金额" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="销售排行榜（按成交金额）">
            <Table
              columns={salesRankColumns}
              dataSource={stats?.sales_rank || []}
              rowKey="user_id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
