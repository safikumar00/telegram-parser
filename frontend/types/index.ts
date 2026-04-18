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
  created_at: string;
}

export interface SignalWithChannel extends Signal {
  channel?: Pick<Channel, "name" | "telegram_id"> | null;
}
