export interface Channel {
  id: string;
  name: string | null;
  telegram_id: string;
  created_at: string;
}

export interface Signal {
  id: string;
  channel_id: string | null;
  pair: string | null;
  entry: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  status: string;
  result_percent: number | null;
  closed_at: string | null;
  created_at: string;
}

export interface SignalWithChannel extends Signal {
  channel?: Pick<Channel, "name" | "telegram_id"> | null;
}

export interface ChannelStats {
  channel_id: string;
  win_rate: number;
  avg_profit: number;
  total_trades: number;
  updated_at?: string;
}

export interface ChannelStatsWithMeta extends ChannelStats {
  channel_name: string | null;
  channel_telegram_id: string | null;
}
