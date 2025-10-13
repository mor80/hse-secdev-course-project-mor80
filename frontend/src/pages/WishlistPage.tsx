import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { wishesApi } from '../api/wishes';
import { Header } from '../components/Header';
import { WishCard } from '../components/WishCard';
import { WishModal } from '../components/WishModal';
import type { Wish, WishCreate } from '../types';

export const WishlistPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingWish, setEditingWish] = useState<Wish | null>(null);
  const [priceFilter, setPriceFilter] = useState<string>('');
  const [page, setPage] = useState(0);
  const pageSize = 12;

  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['wishes', page, priceFilter],
    queryFn: () =>
      wishesApi.getWishes({
        limit: pageSize,
        offset: page * pageSize,
        price_filter: priceFilter ? parseFloat(priceFilter) : undefined,
      }),
  });

  const createMutation = useMutation({
    mutationFn: wishesApi.createWish,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishes'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: WishCreate }) =>
      wishesApi.updateWish(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishes'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: wishesApi.deleteWish,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishes'] });
    },
  });

  const handleOpenModal = () => {
    setEditingWish(null);
    setIsModalOpen(true);
  };

  const handleEditWish = (wish: Wish) => {
    setEditingWish(wish);
    setIsModalOpen(true);
  };

  const handleSubmit = async (data: WishCreate) => {
    if (editingWish) {
      await updateMutation.mutateAsync({ id: editingWish.id, data });
    } else {
      await createMutation.mutateAsync(data);
    }
  };

  const handleDelete = async (id: number) => {
    await deleteMutation.mutateAsync(id);
  };

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Wishlist</h1>
          <button onClick={handleOpenModal} className="btn-primary">
            <svg
              className="w-5 h-5 inline-block mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Add Wish
          </button>
        </div>

        <div className="mb-6 flex items-center space-x-4">
          <div className="flex-1 max-w-xs">
            <label className="label">Filter by max price</label>
            <input
              type="number"
              value={priceFilter}
              onChange={(e) => {
                setPriceFilter(e.target.value);
                setPage(0);
              }}
              className="input"
              placeholder="Max price"
            />
          </div>
          {priceFilter && (
            <button
              onClick={() => {
                setPriceFilter('');
                setPage(0);
              }}
              className="btn-secondary mt-6"
            >
              Clear Filter
            </button>
          )}
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        )}

        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">Failed to load wishes. Please try again.</p>
          </div>
        )}

        {data && data.items.length === 0 && (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No wishes yet</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by adding your first wish.</p>
            <div className="mt-6">
              <button onClick={handleOpenModal} className="btn-primary">
                Add Wish
              </button>
            </div>
          </div>
        )}

        {data && data.items.length > 0 && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.items.map((wish) => (
                <WishCard
                  key={wish.id}
                  wish={wish}
                  onEdit={handleEditWish}
                  onDelete={handleDelete}
                />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="mt-8 flex justify-center items-center space-x-4">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-700">
                  Page {page + 1} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page === totalPages - 1}
                  className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </main>

      <WishModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingWish(null);
        }}
        onSubmit={handleSubmit}
        wish={editingWish}
      />
    </div>
  );
};
