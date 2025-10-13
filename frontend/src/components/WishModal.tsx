import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import type { Wish, WishCreate } from '../types';

interface WishModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: WishCreate) => Promise<void>;
  wish?: Wish | null;
}

export const WishModal = ({ isOpen, onClose, onSubmit, wish }: WishModalProps) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<WishCreate>({
    defaultValues: wish
      ? {
          title: wish.title,
          link: wish.link || undefined,
          price_estimate: wish.price_estimate ? parseFloat(wish.price_estimate) : undefined,
          notes: wish.notes || undefined,
        }
      : {},
  });

  useEffect(() => {
    if (wish) {
      reset({
        title: wish.title,
        link: wish.link || undefined,
        price_estimate: wish.price_estimate ? parseFloat(wish.price_estimate) : undefined,
        notes: wish.notes || undefined,
      });
    } else {
      reset({});
    }
  }, [wish, reset]);

  const handleFormSubmit = async (data: WishCreate) => {
    await onSubmit(data);
    reset();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">{wish ? 'Edit Wish' : 'Add New Wish'}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            disabled={isSubmitting}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <div>
            <label className="label">Title *</label>
            <input
              {...register('title', {
                required: 'Title is required',
                minLength: { value: 1, message: 'Title must be at least 1 character' },
                maxLength: { value: 200, message: 'Title must be at most 200 characters' },
              })}
              className="input"
              placeholder="My dream item"
            />
            {errors.title && <p className="error-message">{errors.title.message}</p>}
          </div>

          <div>
            <label className="label">Link</label>
            <input
              {...register('link', {
                maxLength: { value: 500, message: 'Link must be at most 500 characters' },
              })}
              type="url"
              className="input"
              placeholder="https://example.com/item"
            />
            {errors.link && <p className="error-message">{errors.link.message}</p>}
          </div>

          <div>
            <label className="label">Price Estimate ($)</label>
            <input
              {...register('price_estimate', {
                min: { value: 0, message: 'Price must be positive' },
              })}
              type="number"
              step="0.01"
              className="input"
              placeholder="99.99"
            />
            {errors.price_estimate && (
              <p className="error-message">{errors.price_estimate.message}</p>
            )}
          </div>

          <div>
            <label className="label">Notes</label>
            <textarea
              {...register('notes', {
                maxLength: { value: 1000, message: 'Notes must be at most 1000 characters' },
              })}
              className="input"
              rows={3}
              placeholder="Additional details..."
            />
            {errors.notes && <p className="error-message">{errors.notes.message}</p>}
          </div>

          <div className="flex space-x-3 pt-4">
            <button type="submit" className="btn-primary flex-1" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : wish ? 'Update' : 'Create'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
              disabled={isSubmitting}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
