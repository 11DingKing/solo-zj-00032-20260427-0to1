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
  Tag,
  message,
  Card,
  Timeline,
} from 'antd';
import {
  PlusOutlined,
  FilterOutlined,
  SyncOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import api from '../utils/axios';
import { FollowUpRecord, Customer, FollowUpMethod } from '../types';

const { Option } = Select;
const { TextArea } = Input;

const methodOptions = [
  { value: 'phone', label: '电话' },
  { value: 'visit', label: '拜访' },
  { value: 'wechat', label: '微信' },
  { value: 'email', label: '邮件' },
];

const methodColors: Record<FollowUpMethod, string> = {
  phone: 'blue',
  visit: 'green',
  wechat: 'purple',
  email: 'orange',
};

const FollowUps: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [followUps, setFollowUps] = useState<FollowUpRecord[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [createVisible, setCreateVisible] = useState(false);
  const [form] = Form.useForm();
  
  const [filters, setFilters] = useState({
    customer_id: undefined as number | undefined,
    method: undefined as FollowUpMethod | undefined,
  });

  useEffect(() => {
    fetchCustomers();
    fetchFollowUps();
  }, [page, pageSize, filters]);

  const fetchCustomers = async () => {
    try {
      const response = await api.get('/customers', { params: { page_size: 1000 } });
      setCustomers(response.data.items);
    } catch (error) {
      console.error('Failed to fetch customers:', error);
    }
  };

  const fetchFollowUps = async () => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize,
      };
      
      if (filters.customer_id) params.customer_id = filters.customer_id;
      if (filters.method) params.method = filters.method;

      const response = await api.get('/follow-ups', { params });
      setFollowUps(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to fetch follow-ups:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      const submitData = {
        ...values,
        next_follow_up_time: values.next_follow_up_time ? values.next_follow_up_time.toISOString() : null,
      };
      await api.post('/follow-ups', submitData);
      message.success('跟进记录创建成功');
      setCreateVisible(false);
      form.resetFields();
      fetchFollowUps();
    } catch (error) {
      message.error('创建跟进记录失败');
    }
  };

  const getMethodTag = (method: FollowUpMethod) => {
    const option = methodOptions.find(o => o.value === method);
    const color = methodColors[method] || 'default';
    return <Tag color={color}>{option?.label || method}</Tag>;
  };

  const columns: ColumnsType<FollowUpRecord> = [
    {
      title: '客户',
      dataIndex: 'customer_id',
      key: 'customer_id',
      render: (customerId) => {
        const customer = customers.find(c => c.id === customerId);
        return customer ? customer.company_name : '-';
      },
    },
    {
      title: '跟进方式',
      dataIndex: 'method',
      key: 'method',
      render: (method) => getMethodTag(method),
    },
    {
      title: '跟进内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '下次跟进时间',
      dataIndex: 'next_follow_up_time',
      key: 'next_follow_up_time',
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '创建人',
      dataIndex: 'user_name',
      key: 'user_name',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>跟进记录</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateVisible(true)}>
          新建跟进
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            placeholder="客户"
            style={{ width: 200 }}
            allowClear
            value={filters.customer_id}
            onChange={(v) => setFilters({ ...filters, customer_id: v })}
            showSearch
            optionFilterProp="children"
          >
            {customers.map(c => (
              <Option key={c.id} value={c.id}>{c.company_name}</Option>
            ))}
          </Select>
          <Select
            placeholder="跟进方式"
            style={{ width: 150 }}
            allowClear
            value={filters.method}
            onChange={(v) => setFilters({ ...filters, method: v })}
          >
            {methodOptions.map(o => (
              <Option key={o.value} value={o.value}>{o.label}</Option>
            ))}
          </Select>
          <Button icon={<FilterOutlined />} onClick={fetchFollowUps}>
            筛选
          </Button>
          <Button icon={<SyncOutlined />} onClick={() => {
            setFilters({ customer_id: undefined, method: undefined });
          }}>
            重置
          </Button>
        </Space>
      </Card>

      <Table
        columns={columns}
        dataSource={followUps}
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
        expandable={{
          expandedRowRender: (record) => (
            <div style={{ padding: '0 24px' }}>
              <h4>跟进内容详情：</h4>
              <p>{record.content}</p>
            </div>
          ),
        }}
      />

      <Modal
        title="新建跟进记录"
        open={createVisible}
        onCancel={() => setCreateVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Form.Item
            name="customer_id"
            label="客户"
            rules={[{ required: true, message: '请选择客户' }]}
          >
            <Select placeholder="请选择客户" showSearch optionFilterProp="children">
              {customers.map(c => (
                <Option key={c.id} value={c.id}>{c.company_name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="method"
            label="跟进方式"
            rules={[{ required: true, message: '请选择跟进方式' }]}
          >
            <Select placeholder="请选择跟进方式">
              {methodOptions.map(o => (
                <Option key={o.value} value={o.value}>{o.label}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="content"
            label="跟进内容"
            rules={[{ required: true, message: '请输入跟进内容' }]}
          >
            <TextArea rows={4} placeholder="请输入跟进内容" />
          </Form.Item>
          <Form.Item name="next_follow_up_time" label="下次跟进时间">
            <DatePicker
              showTime
              style={{ width: '100%' }}
              placeholder="请选择下次跟进时间"
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FollowUps;
