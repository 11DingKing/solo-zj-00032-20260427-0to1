import React, { useState } from 'react';
import { Form, Input, Button, Card, Tabs, message, Space } from 'antd';
import { UserOutlined, LockOutlined, CompanyOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store';
import { AuthState } from '../types';

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthenticated) {
    navigate('/dashboard');
    return null;
  }

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', values.username);
      formData.append('password', values.password);

      const response = await axios.post('/api/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const authData: AuthState = response.data;
      login(authData);
      message.success('登录成功');
      navigate('/dashboard');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: {
    company_name: string;
    admin_email: string;
    admin_name: string;
    admin_password: string;
    confirm_password: string;
  }) => {
    if (values.admin_password !== values.confirm_password) {
      message.error('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    try {
      const { confirm_password, ...registerData } = values;
      await axios.post('/api/register', registerData);
      message.success('注册成功，请使用管理员邮箱登录');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  const loginForm = (
    <Form
      name="login"
      onFinish={handleLogin}
      autoComplete="off"
      size="large"
    >
      <Form.Item
        name="username"
        rules={[{ required: true, message: '请输入邮箱' }, { type: 'email', message: '请输入有效的邮箱地址' }]}
      >
        <Input prefix={<UserOutlined />} placeholder="邮箱" />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[{ required: true, message: '请输入密码' }]}
      >
        <Input.Password prefix={<LockOutlined />} placeholder="密码" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} block>
          登录
        </Button>
      </Form.Item>
    </Form>
  );

  const registerForm = (
    <Form
      name="register"
      onFinish={handleRegister}
      autoComplete="off"
      size="large"
    >
      <Form.Item
        name="company_name"
        rules={[{ required: true, message: '请输入公司名称' }]}
      >
        <Input prefix={<CompanyOutlined />} placeholder="公司名称" />
      </Form.Item>

      <Form.Item
        name="admin_email"
        rules={[{ required: true, message: '请输入管理员邮箱' }, { type: 'email', message: '请输入有效的邮箱地址' }]}
      >
        <Input prefix={<UserOutlined />} placeholder="管理员邮箱" />
      </Form.Item>

      <Form.Item
        name="admin_name"
        rules={[{ required: true, message: '请输入管理员姓名' }]}
      >
        <Input prefix={<UserOutlined />} placeholder="管理员姓名" />
      </Form.Item>

      <Form.Item
        name="admin_password"
        rules={[
          { required: true, message: '请输入密码' },
          { min: 6, message: '密码至少6个字符' },
        ]}
      >
        <Input.Password prefix={<LockOutlined />} placeholder="密码（至少6位）" />
      </Form.Item>

      <Form.Item
        name="confirm_password"
        rules={[{ required: true, message: '请确认密码' }]}
      >
        <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} block>
          注册新租户
        </Button>
      </Form.Item>
    </Form>
  );

  const items = [
    {
      key: 'login',
      label: '登录',
      children: loginForm,
    },
    {
      key: 'register',
      label: '注册新租户',
      children: registerForm,
    },
  ];

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        style={{ width: 420, boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
        title={
          <div style={{ textAlign: 'center', fontSize: 24, fontWeight: 'bold' }}>
            多租户 CRM 系统
          </div>
        }
      >
        <Tabs defaultActiveKey="login" items={items} centered />
      </Card>
    </div>
  );
};

export default Login;
