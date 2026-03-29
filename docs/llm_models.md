# Available LLM Models (OpenRouter)

> Generated 2026-03-29. Prices are per-token (input/output).

## Recommended for Meridian

### Production (quality-first)
| Model ID | Context | Input | Output | Notes |
|---|---|---|---|---|
| `anthropic/claude-sonnet-4.6` | 1M | $3.00/M | $15.00/M | Best coding model, latest |
| `anthropic/claude-sonnet-4` | 200K | $3.00/M | $15.00/M | Stable, well-tested |
| `openai/gpt-5` | 400K | $1.25/M | $10.00/M | Strong alternative |
| `google/gemini-2.5-pro` | 1M | $1.25/M | $10.00/M | Good for long JDs/CVs |

### Cost-optimized (volume testing)
| Model ID | Context | Input | Output | Notes |
|---|---|---|---|---|
| `anthropic/claude-haiku-4.5` | 200K | $1.00/M | $5.00/M | Fast, cheap, decent quality |
| `deepseek/deepseek-chat` | 164K | $0.32/M | $0.89/M | Very cheap, good JSON output |
| `deepseek/deepseek-v3.2` | 164K | $0.26/M | $0.38/M | Cheapest capable model |
| `google/gemini-2.5-flash` | 1M | $0.30/M | $2.50/M | Fast, huge context |
| `openai/gpt-4.1-mini` | 1M | $0.40/M | $1.60/M | Good balance |
| `qwen/qwen3-235b-a22b-2507` | 262K | $0.07/M | $0.10/M | Extremely cheap |

### Reasoning (complex evaluation)
| Model ID | Context | Input | Output | Notes |
|---|---|---|---|---|
| `anthropic/claude-opus-4.6` | 1M | $5.00/M | $25.00/M | Deepest reasoning |
| `openai/o3` | 200K | $2.00/M | $8.00/M | Strong reasoning |
| `deepseek/deepseek-r1-0528` | 164K | $0.45/M | $2.15/M | Cheap reasoning |

### Free (development/testing only)
| Model ID | Context | Notes |
|---|---|---|
| `google/gemma-3-27b-it:free` | 131K | Best free model |
| `meta-llama/llama-3.3-70b-instruct:free` | 65K | Good free alternative |
| `qwen/qwen3-coder:free` | 262K | Free coding model |

## Cost Estimate per Meridian Run

One full Stage C run (1 JD extraction + 3 CV assessments):
- Input: ~8K tokens (JD) + 3x ~4K tokens (CVs) = ~20K tokens
- Output: ~2K tokens (requirements) + 3x ~3K tokens (assessments) = ~11K tokens

| Model | Cost per run | 10 scenarios |
|---|---|---|
| claude-sonnet-4.6 | ~$0.22 | ~$2.25 |
| deepseek-chat | ~$0.016 | ~$0.16 |
| deepseek-v3.2 | ~$0.009 | ~$0.09 |
| gemini-2.5-flash | ~$0.033 | ~$0.33 |
| claude-haiku-4.5 | ~$0.075 | ~$0.75 |

## Environment Variables

```bash
export OPENROUTER_API_KEY="sk-or-..."
export DEEPSEEK_API_KEY="sk-..."
```

## Provider Direct APIs

| Provider | Base URL | Env Var |
|---|---|---|
| Anthropic | `https://api.anthropic.com/v1/messages` | `ANTHROPIC_API_KEY` |
| OpenRouter | `https://openrouter.ai/api/v1/chat/completions` | `OPENROUTER_API_KEY` |
| DeepSeek | `https://api.deepseek.com/v1/chat/completions` | `DEEPSEEK_API_KEY` |
