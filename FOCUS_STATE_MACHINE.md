# Focus Session State Machine

## State Definitions

| State | Description | UI Behavior |
|-------|-------------|-------------|
| `idle` | No session started | Show time selector, task selection enabled |
| `running` | Timer counting down | Lock UI, show pause/abandon buttons |
| `paused` | Temporarily interrupted | Show resume/abandon buttons |
| `completed` | Time box finished normally | Show completion card, single next action |
| `abandoned` | User stopped early | Return to idle, save session as abandoned |

## State Transition Table

| From State | Action | To State | Conditions |
|------------|--------|----------|------------|
| `idle` | `start(duration)` | `running` | duration > 0 |
| `running` | `pause()` | `paused` | timer > 0 |
| `running` | `abandon()` | `abandoned` | - |
| `running` | `complete()` | `completed` | timer === 0 (auto) |
| `paused` | `resume()` | `running` | - |
| `paused` | `abandon()` | `abandoned` | - |
| `completed` | `reset()` | `idle` | - |
| `abandoned` | `reset()` | `idle` | - |

## UI Locking Rules

### When `focusState === "running"`:
- ✅ **Disabled**: Add Task input
- ✅ **Disabled**: Task selection
- ✅ **Disabled**: Time box selector
- ✅ **Collapsed/Locked**: Task Pool
- ✅ **Visible**: Pause button, Abandon button
- ✅ **Hidden**: Start button, Resume button

### When `focusState === "paused"`:
- ✅ **Disabled**: Add Task input
- ✅ **Disabled**: Task selection
- ✅ **Disabled**: Time box selector
- ✅ **Collapsed/Locked**: Task Pool
- ✅ **Visible**: Resume button, Abandon button
- ✅ **Hidden**: Start button, Pause button

### When `focusState === "idle"`:
- ✅ **Enabled**: All UI elements
- ✅ **Visible**: Start button, Time selector
- ✅ **Hidden**: Pause, Resume, Abandon buttons

### When `focusState === "completed"`:
- ✅ **Replaced**: Timer view with completion card
- ✅ **Single Action**: "Plan next focus" or "Back to tasks"
- ✅ **Shows**: Duration, completion message

## Button Visibility Matrix

| State | Start | Pause | Resume | Abandon | Reset |
|-------|-------|-------|--------|---------|-------|
| `idle` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `running` | ❌ | ✅ | ❌ | ✅ | ❌ |
| `paused` | ❌ | ❌ | ✅ | ✅ | ❌ |
| `completed` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `abandoned` | ✅ | ❌ | ❌ | ❌ | ✅ |
