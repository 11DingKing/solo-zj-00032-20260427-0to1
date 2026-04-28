import React, { useState } from "react";
import {
  Card,
  Button,
  Upload,
  message,
  Tabs,
  Progress,
  Alert,
  List,
  Space,
  Typography,
} from "antd";
import {
  UploadOutlined,
  DownloadOutlined,
  FileTextOutlined,
} from "@ant-design/icons";
import type { UploadProps } from "antd";
import api from "../utils/axios";
import { ImportResult } from "../types";

const { Text } = Typography;

const downloadFile = async (url: string, filename: string) => {
  try {
    const response = await api.get(url, {
      responseType: "blob",
    });

    const blob = new Blob([response.data], {
      type: "text/csv;charset=utf-8;",
    });
    const link = document.createElement("a");
    const href = URL.createObjectURL(blob);
    link.href = href;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(href);

    message.success("下载成功");
  } catch (error) {
    console.error("Download failed:", error);
    message.error("下载失败，请重试");
  }
};

const ImportExport: React.FC = () => {
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const downloadTemplate = () => {
    downloadFile("/import/template", "客户导入模板.csv");
  };

  const exportCustomers = () => {
    downloadFile(
      "/export/customers",
      `客户数据_${new Date().toISOString().slice(0, 10)}.csv`,
    );
  };

  const exportOpportunities = () => {
    downloadFile(
      "/export/opportunities",
      `商机数据_${new Date().toISOString().slice(0, 10)}.csv`,
    );
  };

  const uploadProps: UploadProps = {
    name: "file",
    accept: ".csv",
    showUploadList: false,
    beforeUpload: (file) => {
      if (!file.name.toLowerCase().endsWith(".csv")) {
        message.error("请上传 CSV 格式文件");
        return false;
      }
      return true;
    },
    customRequest: async (options) => {
      const { file, onSuccess, onError, onProgress } = options;

      setImporting(true);
      setUploadProgress(0);
      setImportResult(null);

      try {
        const formData = new FormData();
        formData.append("file", file as File);

        onProgress?.({ percent: 50 });
        setUploadProgress(50);

        const response = await api.post("/import/customers", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        onProgress?.({ percent: 100 });
        setUploadProgress(100);
        onSuccess?.("ok");

        setImportResult(response.data);

        if (response.data.success > 0 && response.data.failed === 0) {
          message.success(`成功导入 ${response.data.success} 条数据`);
        } else if (response.data.success > 0) {
          message.warning(
            `成功导入 ${response.data.success} 条，失败 ${response.data.failed} 条`,
          );
        } else {
          message.error("导入失败，请检查文件格式");
        }
      } catch (error: any) {
        onError?.(error);
        message.error(
          "导入失败：" + (error.response?.data?.detail || "未知错误"),
        );
      } finally {
        setImporting(false);
      }
    },
  };

  const tabItems = [
    {
      key: "import",
      label: "导入数据",
      children: (
        <Card>
          <Alert
            message="导入说明"
            description={
              <div>
                <p>1. 请先下载导入模板，按照模板格式填写数据</p>
                <p>2. 支持 CSV 格式文件</p>
                <p>3. 字段映射说明：</p>
                <ul>
                  <li>公司名称（必填）、行业、规模、地址、官网、备注</li>
                  <li>联系人姓名、职位、电话、邮箱、微信</li>
                </ul>
              </div>
            }
            type="info"
            style={{ marginBottom: 24 }}
          />

          <Space style={{ marginBottom: 24 }}>
            <Button icon={<DownloadOutlined />} onClick={downloadTemplate}>
              下载导入模板
            </Button>
            <Upload {...uploadProps}>
              <Button
                type="primary"
                icon={<UploadOutlined />}
                loading={importing}
              >
                上传 CSV 文件
              </Button>
            </Upload>
          </Space>

          {importing && (
            <Card size="small" style={{ marginBottom: 24 }}>
              <Progress percent={uploadProgress} status="active" />
              <Text type="secondary">正在导入数据，请稍候...</Text>
            </Card>
          )}

          {importResult && (
            <Card title="导入结果" size="small">
              <Space size="large" style={{ marginBottom: 16 }}>
                <div>
                  <Text strong>总计：</Text>
                  <Text style={{ marginLeft: 8 }}>{importResult.total} 条</Text>
                </div>
                <div>
                  <Text strong style={{ color: "#52c41a" }}>
                    成功：
                  </Text>
                  <Text style={{ marginLeft: 8, color: "#52c41a" }}>
                    {importResult.success} 条
                  </Text>
                </div>
                <div>
                  <Text strong style={{ color: "#f5222d" }}>
                    失败：
                  </Text>
                  <Text style={{ marginLeft: 8, color: "#f5222d" }}>
                    {importResult.failed} 条
                  </Text>
                </div>
              </Space>

              {importResult.errors.length > 0 && (
                <div>
                  <Text strong style={{ color: "#f5222d" }}>
                    错误详情：
                  </Text>
                  <List
                    size="small"
                    dataSource={importResult.errors.slice(0, 20)}
                    renderItem={(error: any) => (
                      <List.Item>
                        <Text type="danger">{error.message}</Text>
                      </List.Item>
                    )}
                  />
                  {importResult.errors.length > 20 && (
                    <Text type="secondary">
                      ... 还有 {importResult.errors.length - 20} 条错误
                    </Text>
                  )}
                </div>
              )}
            </Card>
          )}
        </Card>
      ),
    },
    {
      key: "export",
      label: "导出数据",
      children: (
        <Card>
          <Alert
            message="导出说明"
            description={
              <div>
                <p>
                  1. 客户数据导出：包含客户基本信息、联系人信息、状态、负责人等
                </p>
                <p>2. 商机数据导出：包含商机基本信息、客户名称、阶段、金额等</p>
                <p>3. 导出格式为 CSV，可直接用 Excel 打开</p>
              </div>
            }
            type="info"
            style={{ marginBottom: 24 }}
          />

          <Space>
            <Card
              size="small"
              style={{ width: 200, cursor: "pointer" }}
              hoverable
              onClick={exportCustomers}
            >
              <div style={{ textAlign: "center" }}>
                <FileTextOutlined style={{ fontSize: 48, color: "#1890ff" }} />
                <div style={{ marginTop: 16, fontWeight: "bold" }}>
                  导出客户数据
                </div>
                <Button type="link" icon={<DownloadOutlined />}>
                  点击下载
                </Button>
              </div>
            </Card>

            <Card
              size="small"
              style={{ width: 200, cursor: "pointer" }}
              hoverable
              onClick={exportOpportunities}
            >
              <div style={{ textAlign: "center" }}>
                <FileTextOutlined style={{ fontSize: 48, color: "#52c41a" }} />
                <div style={{ marginTop: 16, fontWeight: "bold" }}>
                  导出商机数据
                </div>
                <Button type="link" icon={<DownloadOutlined />}>
                  点击下载
                </Button>
              </div>
            </Card>
          </Space>
        </Card>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据导入导出</h2>
      <Tabs defaultActiveKey="import" items={tabItems} />
    </div>
  );
};

export default ImportExport;
