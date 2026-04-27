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
  Descriptions,
  Tabs,
  Timeline,
  Card,
  List,
} from 'antd';
import {
  PlusOutlined,
  FilterOutlined,
  SyncOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';
import api from '../utils/axios';
import { Customer, Contact, CustomerStatus, CustomerStatusLog, User } from '../types';
import { useAuthStore } from '../store';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

const statusOptions = [
  { value: 'potential', label: '潜在客户', color: 'blue' },
  { value: 'interested', label: '意向客户', color: 'green' },
  { value: 'opportunity', label: '商机客户', color: 'orange' },
  { value: 'closed', label: '成交客户', color: 'success' },
  { value: 'lost', label: '流失客户', color: 'error' },
];

const methodLabels: Record<string, string> = {
  phone: '电话',
  visit: '拜访',
  wechat: '微信',
  email: '邮件',
};

interface CustomersProps {
  customerId?: string;
}

const Customers: React.FC<CustomersProps> = ({ customerId }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [editVisible, setEditVisible] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [statusLogs, setStatusLogs] = useState<CustomerStatusLog[]>([]);
  const [form] = Form.useForm();
  const [contactForm] = Form.useForm();
  
  const [filters, setFilters] = useState({
    industry: undefined as string | undefined,
    scale: undefined as string | undefined,
    status: undefined as CustomerStatus | undefined,
    owner_id: undefined as number | undefined,
    created_at_start: undefined as Dayjs | undefined,
    created_at_end: undefined as Dayjs | undefined,
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  const isAdmin = useAuthStore((state) => state.role) === 'admin';

  useEffect(() => {
    fetchUsers();
    fetchCustomers();
  }, [page, pageSize, filters]);

  useEffect(() => {
    if (customerId) {
      fetchCustomerDetail(parseInt(customerId));
    }
  }, [customerId]);

  const fetchUsers = async () => {
    try {
      const response = await api.get('/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize,
        sort_by: filters.sort_by,
        sort_order: filters.sort_order,
      };
      
      if (filters.industry) params.industry = filters.industry;
      if (filters.scale) params.scale = filters.scale;
      if (filters.status) params.status = filters.status;
      if (filters.owner_id) params.owner_id = filters.owner_id;
      if (filters.created_at_start) {
        params.created_at_start = filters.created_at_start.toISOString();
      }
      if (filters.created_at_end) {
        params.created_at_end = filters.created_at_end.toISOString();
      }

      const response = await api.get('/customers', { params });
      setCustomers(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to fetch customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomerDetail = async (id: number) => {
    try {
      const response = await api.get(`/customers/${id}`);
      setSelectedCustomer(response.data);
      setDetailVisible(true);
      
      fetchContacts(id);
      fetchStatusLogs(id);
    } catch (error) {
      console.error('Failed to fetch customer detail:', error);
    }
  };

  const fetchContacts = async (customerId: number) => {
    try {
      const response = await api.get(`/customers/${customerId}/contacts`);
      setContacts(response.data);
    } catch (error) {
      console.error('Failed to fetch contacts:', error);
    }
  };

  const fetchStatusLogs = async (customerId: number) => {
    try {
      const response = await api.get(`/customers/${customerId}/status-logs`);
      setStatusLogs(response.data);
    } catch (error) {
      console.error('Failed to fetch status logs:', error);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      await api.post('/customers', values);
      message.success('客户创建成功');
      setCreateVisible(false);
      form.resetFields();
      fetchCustomers();
    } catch (error) {
      message.error('创建客户失败');
    }
  };

  const handleEdit = async (values: any) => {
    if (!selectedCustomer) return;
    try {
      await api.put(`/customers/${selectedCustomer.id}`, values);
      message.success('客户更新成功');
      setEditVisible(false);
      fetchCustomers();
      fetchCustomerDetail(selectedCustomer.id);
    } catch (error) {
      message.error('更新客户失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/customers/${id}`);
      message.success('客户删除成功');
      fetchCustomers();
    } catch (error) {
      message.error('删除客户失败');
    }
  };

  const handleAddContact = async (values: any) => {
    if (!selectedCustomer) return;
    try {
      await api.post(`/customers/${selectedCustomer.id}/contacts`, values);
      message.success('联系人添加成功');
      contactForm.resetFields();
      fetchContacts(selectedCustomer.id);
    } catch (error) {
      message.error('添加联系人失败');
    }
  };

  const getStatusTag = (status: CustomerStatus) => {
    const option = statusOptions.find(o => o.value === status);
    return option ? (
      <Tag color={option.color}>{option.label}</Tag>
    ) : status;
  };

  const columns: ColumnsType<Customer> = [
    {
      title: '公司名称',
      dataIndex: 'company_name',
      key: 'company_name',
      render: (text, record) => (
        <a onClick={() => fetchCustomerDetail(record.id)}>{text}</a>
      ),
    },
    {
      title: '行业',
      dataIndex: 'industry',
      key: 'industry',
    },
    {
      title: '规模',
      dataIndex: 'scale',
      key: 'scale',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusTag(status),
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
            icon={<EyeOutlined />}
            onClick={() => fetchCustomerDetail(record.id)}
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedCustomer(record);
              form.setFieldsValue(record);
              setEditVisible(true);
            }}
          />
          {isAdmin && (
            <Popconfirm
              title="确定要删除这个客户吗？"
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

  const customerFormItems = (
    <>
      <Form.Item
        name="company_name"
        label="公司名称"
        rules={[{ required: true, message: '请输入公司名称' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item name="industry" label="行业">
        <Select placeholder="请选择行业" allowClear>
          <Option value="互联网">互联网</Option>
          <Option value="金融">金融</Option>
          <Option value="教育">教育</Option>
          <Option value="医疗">医疗</Option>
          <Option value="制造业">制造业</Option>
          <Option value="零售">零售</Option>
          <Option value="其他">其他</Option>
        </Select>
      </Form.Item>
      <Form.Item name="scale" label="规模">
        <Select placeholder="请选择规模" allowClear>
          <Option value="1-10人">1-10人</Option>
          <Option value="10-50人">10-50人</Option>
          <Option value="50-100人">50-100人</Option>
          <Option value="100-500人">100-500人</Option>
          <Option value="500人以上">500人以上</Option>
        </Select>
      </Form.Item>
      <Form.Item name="address" label="地址">
        <Input />
      </Form.Item>
      <Form.Item name="website" label="官网">
        <Input />
      </Form.Item>
      <Form.Item name="remark" label="备注">
        <TextArea rows={4} />
      </Form.Item>
      <Form.Item name="status" label="状态">
        <Select placeholder="请选择状态">
          {statusOptions.map(o => (
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
    </>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>客户管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateVisible(true)}>
          新建客户
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            placeholder="状态"
            style={{ width: 150 }}
            allowClear
            value={filters.status}
            onChange={(v) => setFilters({ ...filters, status: v })}
          >
            {statusOptions.map(o => (
              <Option key={o.value} value={o.value}>{o.label}</Option>
            ))}
          </Select>
          <Select
            placeholder="行业"
            style={{ width: 150 }}
            allowClear
            value={filters.industry}
            onChange={(v) => setFilters({ ...filters, industry: v })}
          >
            <Option value="互联网">互联网</Option>
            <Option value="金融">金融</Option>
            <Option value="教育">教育</Option>
            <Option value="医疗">医疗</Option>
            <Option value="制造业">制造业</Option>
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
          <RangePicker
            placeholder={['创建开始', '创建结束']}
            onChange={(dates) => {
              if (dates) {
                setFilters({ ...filters, created_at_start: dates[0], created_at_end: dates[1] });
              } else {
                setFilters({ ...filters, created_at_start: undefined, created_at_end: undefined });
              }
            }}
          />
          <Button icon={<FilterOutlined />} onClick={fetchCustomers}>
            筛选
          </Button>
          <Button icon={<SyncOutlined />} onClick={fetchCustomers}>
            重置
          </Button>
        </Space>
      </Card>

      <Table
        columns={columns}
        dataSource={customers}
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
        title="新建客户"
        open={createVisible}
        onCancel={() => setCreateVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{ status: 'potential' }}
        >
          {customerFormItems}
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑客户"
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
          {customerFormItems}
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="客户详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={900}
      >
        {selectedCustomer && (
          <Tabs defaultActiveKey="info">
            <TabPane tab="基本信息" key="info">
              <Descriptions bordered column={2}>
                <Descriptions.Item label="公司名称">{selectedCustomer.company_name}</Descriptions.Item>
                <Descriptions.Item label="状态">{getStatusTag(selectedCustomer.status)}</Descriptions.Item>
                <Descriptions.Item label="行业">{selectedCustomer.industry || '-'}</Descriptions.Item>
                <Descriptions.Item label="规模">{selectedCustomer.scale || '-'}</Descriptions.Item>
                <Descriptions.Item label="地址">{selectedCustomer.address || '-'}</Descriptions.Item>
                <Descriptions.Item label="官网">{selectedCustomer.website || '-'}</Descriptions.Item>
                <Descriptions.Item label="负责人">{selectedCustomer.owner_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {selectedCustomer.created_at ? dayjs(selectedCustomer.created_at).format('YYYY-MM-DD HH:mm') : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="备注" span={2}>
                  {selectedCustomer.remark || '-'}
                </Descriptions.Item>
              </Descriptions>
            </TabPane>

            <TabPane tab="联系人" key="contacts">
              <div style={{ marginBottom: 16 }}>
                <Button
                  type="primary"
                  size="small"
                  icon={<PlusOutlined />}
                  onClick={() => contactForm.resetFields()}
                >
                  添加联系人
                </Button>
              </div>
              
              <Form form={contactForm} layout="vertical" onFinish={handleAddContact} style={{ marginBottom: 24 }}>
                <Card size="small" title="新建联系人" style={{ marginBottom: 16 }}>
                  <Space wrap>
                    <Form.Item name="name" label="姓名" rules={[{ required: true }]} style={{ marginBottom: 0, width: 150 }}>
                      <Input size="small" />
                    </Form.Item>
                    <Form.Item name="position" label="职位" style={{ marginBottom: 0, width: 150 }}>
                      <Input size="small" />
                    </Form.Item>
                    <Form.Item name="phone" label="电话" style={{ marginBottom: 0, width: 150 }}>
                      <Input size="small" />
                    </Form.Item>
                    <Form.Item name="email" label="邮箱" style={{ marginBottom: 0, width: 150 }}>
                      <Input size="small" />
                    </Form.Item>
                    <Form.Item name="wechat" label="微信" style={{ marginBottom: 0, width: 150 }}>
                      <Input size="small" />
                    </Form.Item>
                    <Form.Item style={{ marginBottom: 0 }}>
                      <Button type="primary" size="small" htmlType="submit">
                        添加
                      </Button>
                    </Form.Item>
                  </Space>
                </Card>
              </Form>

              <List
                dataSource={contacts}
                renderItem={(contact) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <Space>
                          <span style={{ fontWeight: 'bold' }}>{contact.name}</span>
                          {contact.is_primary === 'true' && <Tag color="blue">主要</Tag>}
                        </Space>
                      }
                      description={
                        <Space wrap>
                          {contact.position && <span>职位: {contact.position}</span>}
                          {contact.phone && <span>电话: {contact.phone}</span>}
                          {contact.email && <span>邮箱: {contact.email}</span>}
                          {contact.wechat && <span>微信: {contact.wechat}</span>}
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </TabPane>

            <TabPane tab="状态变更记录" key="logs">
              <Timeline>
                {statusLogs.map((log, index) => (
                  <Timeline.Item key={log.id}>
                    <p>
                      状态变更: {statusOptions.find(o => o.value === log.old_status)?.label} → {statusOptions.find(o => o.value === log.new_status)?.label}
                    </p>
                    <p>操作人: {log.user_name || '-'}</p>
                    <p>时间: {log.created_at ? dayjs(log.created_at).format('YYYY-MM-DD HH:mm') : '-'}</p>
                    {log.remark && <p>备注: {log.remark}</p>}
                  </Timeline.Item>
                ))}
              </Timeline>
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default Customers;
