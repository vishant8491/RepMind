import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../api/client';

export const fetchInteractions = createAsyncThunk(
  'interactions/fetchAll',
  async (hcpName = '') => {
    const params = hcpName ? { hcp_name: hcpName } : {};
    const res = await apiClient.get('/api/interactions', { params });
    return res.data;
  }
);

export const createInteraction = createAsyncThunk(
  'interactions/create',
  async (payload, { rejectWithValue }) => {
    try {
      const res = await apiClient.post('/api/interactions', payload);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to create interaction.');
    }
  }
);

export const updateInteraction = createAsyncThunk(
  'interactions/update',
  async ({ id, changes }, { rejectWithValue }) => {
    try {
      const res = await apiClient.put(`/api/interactions/${id}`, changes);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to update interaction.');
    }
  }
);

export const deleteInteraction = createAsyncThunk(
  'interactions/delete',
  async (id, { rejectWithValue }) => {
    try {
      await apiClient.delete(`/api/interactions/${id}`);
      return id;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to delete interaction.');
    }
  }
);

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: {
    items: [],
    status: 'idle', 
    error: null,
    editingId: null, 
  },
  reducers: {
    setEditingId(state, action) {
      state.editingId = action.payload;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
        state.editingId = null;
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.error = action.payload;
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        const idx = state.items.findIndex((i) => i.id === action.payload.id);
        if (idx !== -1) state.items[idx] = action.payload;
        state.editingId = null;
      })
      .addCase(updateInteraction.rejected, (state, action) => {
        state.error = action.payload;
      })
      .addCase(deleteInteraction.fulfilled, (state, action) => {
        state.items = state.items.filter((i) => i.id !== action.payload);
      })
      .addCase(deleteInteraction.rejected, (state, action) => {
        state.error = action.payload;
      });
  },
});

export const { setEditingId, clearError } = interactionsSlice.actions;
export default interactionsSlice.reducer;
