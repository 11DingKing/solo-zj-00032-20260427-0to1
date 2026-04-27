import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Input,
  Select,
  DatePicker,
  Space,
  Modal,
  Form,
  InputNumber,
  Tag,
  message,
  Popconfirm,
  Card,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  FilterOutlined,
  SyncOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import api from '../utils/axios';
import { Opportunity, Customer, OpportunityStage, User } from '../types';
import { useAuthStore } from '../store';

const { Option } = Select;
const { TextArea } = Input;

const stageOptions = [
  { value: 'initial_contact', label: '初步接触', color: 'blue' },
  { value: 'requirement_confirmation', label: '需求确认', color: 'cyan' },
  { value: 'proposal_quote', label: '方案报价', color: 'purple' },
  { value: 'negotiation', label: '商务谈判', color: 'orange' },
  { value: 'won', label: '赢单', color: 'success' },
  { value: 'lost', label: '输单', color: 'error' },
];

const Opportunities: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [funnelData, setFunnelData] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [createVisible, setCreateVisible] = useState(false);
  const [editVisible, setEditVisible] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [form] = Form.useForm();
  
  const [filters, setFilters] = useState({
    stage: undefined as OpportunityStage | undefined,
    owner_id: undefined as number | undefined,
  });

  const isAdmin = useAuthStore((state) => state.role) === 'admin';

  useEffect(() => {
    fetchCustomers();
    fetchUsers();
    fetchOpportunities();
    fetchFunnel();
  }, [page, pageSize, filters]);

  const fetchCustomers = async () => {
    try {
      const response = await api.get('/customers', { params: { page_size: 1000 } });
      setCustomers(response.data.items);
    } catch (error) {
      console.error('Failed to fetch customers:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get('/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const fetchOpportunities = async () => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize,
      };
      
      if (filters.stage) params.stage = filters.stage;
      if (filters.owner_id) params.owner_id = filters.owner_id;

      const response = await api.get('/opportunities', { params });
      setOpportunities(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to fetch opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFunnel = async () => {
    try {
      const response = await api.get('/opportunity-funnel');
      const data = response.data.map((item: any) => ({
        ...item,
        stage: {
          'initial_contact': '初步接触',
          'requirement_confirmation': '需求确认',
          'proposal_quote': '方案报价',
          'negotiation': '商务谈判',
          'won': '赢单',
          'lost': '输单',
        }[item.stage] || item.stage,
      }));
      setFunnelData(data);
    } catch (error) {
      console.error('Failed to fetch funnel:', error);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      await api.post('/opportunities', values);
      message.success('商机创建成功');
      setCreateVisible(false);
      form.resetFields();
      fetchOpportunities();
      fetchFunnel();
    } catch (error) {
      message.error('创建商机失败');
    }
  };

  const handleEdit = async (values: any) => {
    if (!selectedOpportunity) return;
    try {
      await api.put(`/opportunities/${selectedOpportunity.id}`, values);
      message.success('商机更新成功');
      setEditVisible(false);
      fetchOpportunities();
      fetchFunnel();
    } catch (error) {
      message.error('更新商机失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/opportunities/${id}`);
      message.success('商机删除成功');
      fetchOpportunities();
      fetchFunnel();
    } catch (error) {
      message.error('删除商机失败');
    }
  };

  const getStageTag = (stage: OpportunityStage) => {
    const option = stageOptions.find(o => o.value === stage);
    return option ? (
      <Tag color={option.color}>{option.label}</Tag>
    ) : stage;
  };

  const columns: ColumnsType<Opportunity> = [
    {
      title: '商机名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '客户',
      dataIndex: 'customer_name',
      key: 'customer_name',
    },
    {
      title: '预计金额',
      dataIndex: 'expected_amount',
      key: 'expected_amount',
      render: (value) => value ? `¥${value.toLocaleString()}` : '-',
    },
    {
      title: '预计成交日期',
      dataIndex: 'expected_close_date',
      key: 'expected_close_date',
      render: (text) => text || '-',
    },
    {
      title: '阶段',
      dataIndex: 'stage',
      key: 'stage',
      render: (stage) => getStageTag(stage),
    },
    {
      title: '负责人',
      dataIndex: 'owner_name',
      key: 'owner_name',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedOpportunity(record);
              form.setFieldsValue({
                ...record,
                expected_close_date: record.expected_close_date ? dayjs(record.expected_close_date) : undefined,
              });
              setEditVisible(true);
            }}
          />
          {isAdmin && (
            <Popconfirm
              title="确定要删除这个商机吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="text" icon={<DeleteOutlined />} danger />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  const formItems = (
    <>
      <Form.Item
        name="name"
        label="商机名称"
        rules={[{ required: true, message: '请输入商机名称' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="customer_id"
        label="客户"
        rules={[{ required: true, message: '请选择客户' }]}
      >
        <Select placeholder="请选择客户">
          {customers.map(c => (
            <Option key={c.id} value={c.id}>{c.company_name}</Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item name="expected_amount" label="预计金额">
        <InputNumber
          style={{ width: '100%' }}
          min={0}
          precision={2}
          prefix="¥"
          placeholder="请输入预计金额"
        />
      </Form.Item>
      <Form.Item name="expected_close_date" label="预计成交日期">
        <DatePicker style={{ width: '100%' }} placeholder="请选择预计成交日期" />
      </Form.Item>
      <Form.Item name="stage" label="阶段">
        <Select placeholder="请选择阶段">
          {stageOptions.map(o => (
            <Option key={o.value} value={o.value}>{o.label}</Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item name="owner_id" label="负责人">
        <Select placeholder="请选择负责人" allowClear>
          {users.map(u => (
            <Option key={u.id} value={u.id}>{u.name}</Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item name="competitor_info" label="竞争对手信息">
        <TextArea rows={4} placeholder="请输入竞争对手信息" />
      </Form.Item>
    </>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>商机管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateVisible(true)}>
          新建商机
        </Button>
      </div>

      <Card title="商机漏斗图" style={{ marginBottom: 16 }}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={funnelData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="stage" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#1890ff" name="商机数量" />
            <Bar dataKey="amount" fill="#52c41a" name="预计金额(万)" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            placeholder="阶段"
            style={{ width: 150 }}
            allowClear
            value={filters.stage}
            onChange={(v) => setFilters({ ...filters, stage: v })}
          >
            {stageOptions.map(o => (
              <Option key={o.value} value={o.value}>{o.label}</Option>
            ))}
          </Select>
          <Select
            placeholder="负责人"
            style={{ width: 150 }}
            allowClear
            value={filters.owner_id}
            onChange={(v) => setFilters({ ...filters, owner_id: v })}
          >
            {users.map(u => (
              <Option key={u.id} value={u.id}>{u.name}</Option>
            ))}
          </Select>
          <Button icon={<FilterOutlined />} onClick={fetchOpportunities}>
            筛选
          </Button>
          <Button icon={<SyncOutlined />} onClick={() => {
            setFilters({ stage: undefined, owner_id: undefined });
            fetchFunnel();
          }}>
            重置
          </Button>
        </Space>
      </Card>

      <Table
        columns={columns}
        dataSource={opportunities}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (p, ps) => {
            setPage(p);
            setPageSize(ps);
          },
        }}
      />

      <Modal
        title="新建商机"
        open={createVisible}
        onCancel={() => setCreateVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{ stage: 'initial_contact' }}
        >
          {formItems}
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑商机"
        open={editVisible}
        onCancel={() => setEditVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEdit}
        >
          {formItems}
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Opportunities;
