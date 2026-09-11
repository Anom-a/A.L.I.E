export interface NavItem {
  icon: string;
  label: string;
  isActive?: boolean;
}

export interface SessionItem {
  name: string;
  time: string;
  status: 'active' | 'success' | 'pending';
}

export interface SourceItem {
  id: string;
  title: string;
  journal: string;
  year: string;
  score: string;
  doi?: string;
  reportId?: string;
}
