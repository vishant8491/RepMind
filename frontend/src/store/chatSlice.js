import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../api/client';

const THREAD_ID = 'rep-session-1';

export const sendChatMessage = createAsyncThunk(
  'chat/send',
  async (message, { rejectWithValue }) => {
    try {
      const res = await apiClient.post('/api/chat', { message, thread_id: THREAD_ID });
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'The AI Assistant could not respond.');
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [
      {
        role: 'assistant',
        content:
          "Log interaction details here (e.g. \"Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure\") or ask for help.",
        toolCalls: [],
      },
    ],
    sending: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state, action) => {
        state.sending = true;
        state.error = null;
        state.messages.push({ role: 'user', content: action.meta.arg, toolCalls: [] });
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.sending = false;
        state.messages.push({
          role: 'assistant',
          content: action.payload.reply,
          toolCalls: action.payload.tool_calls || [],
        });
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.sending = false;
        state.error = action.payload;
        state.messages.push({
          role: 'assistant',
          content: `Sorry, something went wrong: ${action.payload}`,
          toolCalls: [],
          isError: true,
        });
      });
  },
});

export default chatSlice.reducer;
