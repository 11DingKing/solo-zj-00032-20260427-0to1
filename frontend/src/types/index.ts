export type UserRole = 'admin' | 'sales' | 'read_only';

export type CustomerStatus = 'potential' | 'interested' | 'opportunity' | 'closed' | 'lost';

export type OpportunityStage = 
  | 'initial_contact' 
  | 'requirement_confirmation' 
  | 'proposal_quote' 
  | 'negotiation' 
  | 'won' 
  | 'lost';

export type FollowUpMethod = 'phone' | 'visit' | 'wechat' | 'email';

export interface User {
  id: number;
  tenant_id: number;
  email: string;
  name: string;
  role: UserRole;
  is_active: string;
  created_at?: string;
}

export interface AuthState {
  access_token: string;
  user_id: number;
  email: string;
  name: string;
  role: UserRole;
  tenant_id: number;
  schema_name: string;
  company_name: string;
}

export interface Contact {
  id: number;
  customer_id: number;
  name: string;
  position?: string;
  phone?: string;
  email?: string;
  wechat?: string;
  is_primary: string;
  created_at?: string;
}

export interface Customer {
  id: number;
  company_name: string;
  industry?: string;
  scale?: string;
  address?: string;
  website?: string;
  remark?: string;
  status: CustomerStatus;
  owner_id?: number;
  owner_name?: string;
  created_at?: string;
  updated_at?: string;
  contacts: Contact[];
}

export interface Opportunity {
  id: number;
  name: string;
  customer_id: number;
  customer_name?: string;
  expected_amount?: number;
  expected_close_date?: string;
  stage: OpportunityStage;
  owner_id?: number;
  owner_name?: string;
  competitor_info?: string;
  created_at?: string;
  updated_at?: string;
}

export interface FollowUpRecord {
  id: number;
  customer_id: number;
  user_id: number;
  user_name?: string;
  method: FollowUpMethod;
  content: string;
  next_follow_up_time?: string;
  created_at?: string;
}

export interface PendingFollowUp {
  id: number;
  customer_id: number;
  customer_name: string;
  next_follow_up_time: string;
  content: string;
}

export interface CustomerStatusLog {
  id: number;
  customer_id: number;
  user_id: number;
  user_name?: string;
  old_status: CustomerStatus;
  new_status: CustomerStatus;
  remark?: string;
  created_at?: string;
}

export interface FunnelItem {
  stage: string;
  count: number;
  amount: number;
}

export interface IndustryDistribution {
  industry: string;
  count: number;
}

export interface SalesRankItem {
  user_id: number;
  user_name: string;
  won_count: number;
  won_amount: number;
}

export interface MonthlyTrendItem {
  month: string;
  amount: number;
}

export interface DashboardStats {
  monthly_new_customers: number;
  monthly_new_opportunity_amount: number;
  sales_rank: SalesRankItem[];
  industry_distribution: IndustryDistribution[];
  opportunity_funnel: FunnelItem[];
  monthly_trend: MonthlyTrendItem[];
}

export interface ImportResult {
  total: number;
  success: number;
  failed: number;
  errors: { message: string }[];
}
