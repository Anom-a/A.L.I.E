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

export type ResearchStatus = 'pending' | 'running' | 'done' | 'failed';

export interface CitationDTO {
  source_url_or_id: string;
  source_name: string;
  retrieved_at: string;
}

export interface ReportSectionDTO {
  title: string;
  content: string;
  citation_ids: string[];
}

export interface ReportDTO {
  query_id: string;
  sections: ReportSectionDTO[];
  citations: CitationDTO[];
  generated_at: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: ResearchStatus;
  error?: string | null;
}

export type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string; // The query or a simple text response
  report?: ReportDTO | null; // For the assistant when report is ready
  status?: ResearchStatus | null; // For the assistant while processing
  error?: string | null; // For the assistant if failed
}
