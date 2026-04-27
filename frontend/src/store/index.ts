import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, User, Customer } from '../types';

interface AuthStore extends AuthState {
  isAuthenticated: boolean;
  login: (data: AuthState) => void;
  logout: () => void;
}

interface AppStore {
  collapsed: boolean;
  toggleCollapsed: () => void;
  pendingFollowUps: any[];
  setPendingFollowUps: (items: any[]) => void;
  users: User[];
  setUsers: (users: User[]) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      access_token: '',
      user_id: 0,
      email: '',
      name: '',
      role: 'sales' as const,
      tenant_id: 0,
      schema_name: '',
      company_name: '',
      isAuthenticated: false,
      login: (data: AuthState) => set({
        ...data,
        isAuthenticated: true,
      }),
      logout: () => set({
        access_token: '',
        user_id: 0,
        email: '',
        name: '',
        role: 'sales',
        tenant_id: 0,
        schema_name: '',
        company_name: '',
        isAuthenticated: false,
      }),
    }),
    {
      name: 'crm-auth-storage',
    }
  )
);

export const useAppStore = create<AppStore>((set) => ({
  collapsed: false,
  toggleCollapsed: () => set((state) => ({ collapsed: !state.collapsed })),
  pendingFollowUps: [],
  setPendingFollowUps: (items) => set({ pendingFollowUps: items }),
  users: [],
  setUsers: (users) => set({ users }),
}));
