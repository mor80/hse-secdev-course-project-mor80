import type { Wish, WishCreate, WishListResponse, WishUpdate } from '../types';
import { apiClient } from './client';

interface GetWishesParams {
  limit?: number;
  offset?: number;
  price_filter?: number;
}

export const wishesApi = {
  getWishes: async (params: GetWishesParams = {}): Promise<WishListResponse> => {
    const response = await apiClient.get<WishListResponse>('/api/v1/wishes/', { params });
    return response.data;
  },

  getWish: async (id: number): Promise<Wish> => {
    const response = await apiClient.get<Wish>(`/api/v1/wishes/${id}`);
    return response.data;
  },

  createWish: async (data: WishCreate): Promise<Wish> => {
    const response = await apiClient.post<Wish>('/api/v1/wishes/', data);
    return response.data;
  },

  updateWish: async (id: number, data: WishUpdate): Promise<Wish> => {
    const response = await apiClient.patch<Wish>(`/api/v1/wishes/${id}`, data);
    return response.data;
  },

  deleteWish: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/wishes/${id}`);
  },
};
