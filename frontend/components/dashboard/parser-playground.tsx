"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { parseSignal, type ParsedSignal } from "@/lib/parser";
import { Sparkles } from "lucide-react";

const EXAMPLES = [
  "🔥 BTC/USDT LONG Entry: 62000 - 62500 SL: 61500 TP1: 63000 TP2: 64000",
  "BUY BTC 62000 SL 61500 TP 64000",
  "ETH/USDT Entry 3200 Stop Loss 3100 Take Profit 3400",
];

export function ParserPlayground() {
  const [input, setInput] = useState(EXAMPLES[0]);
  const result = useMemo<ParsedSignal>(() => parseSignal(input), [input]);

  const isValid = Boolean(result.pair && result.entry !== null);

  return (
    <Card data-testid="parser-playground" className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between gap-4 border-b border-border/50 pb-5">
        <div>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Sparkles className="h-4 w-4 text-indigo-500" strokeWidth={1.75} />
            Parser sandbox
          </CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            Test <code className="font-mono text-xs">parseSignal()</code> against
            real broker copy.
          </p>
        </div>
      </CardHeader>
      <CardContent className="space-y-5 p-6">
        <Input
          data-testid="parser-playground-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Paste a Telegram signal…"
          className="font-mono text-[13px]"
        />

        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex, i) => (
            <Button
              key={ex}
              size="sm"
              variant="outline"
              data-testid={`parser-example-${i}`}
              onClick={() => setInput(ex)}
            >
              Example {i + 1}
            </Button>
          ))}
        </div>

        <div
          data-testid="parser-result"
          className="rounded-2xl border border-border/60 bg-[#0B0C18] p-5 font-mono text-[12px] leading-relaxed text-white/85"
        >
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-[0.18em] text-white/40">
              result
            </span>
            <Badge
              variant={isValid ? "success" : "warning"}
              data-testid="parser-result-badge"
              className="rounded-full font-sans text-[10px] uppercase tracking-wider"
            >
              {isValid ? "valid" : "ignored"}
            </Badge>
          </div>
          <pre className="whitespace-pre-wrap text-white/90">
{JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </CardContent>
    </Card>
  );
}
