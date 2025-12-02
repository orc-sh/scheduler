import { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import api from '@/lib/api';

const BillingCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const hostedPageId = searchParams.get('hosted_page_id');

    const syncSubscription = async () => {
      try {
        await api.post('/api/subscriptions/sync-from-chargebee', {
          hosted_page_id: hostedPageId,
        });

        toast('Plan upgraded', {
          description: 'Your subscription has been updated.',
        });
      } catch (error: any) {
        const description =
          error?.response?.data?.detail ||
          error?.message ||
          'Failed to confirm subscription upgrade.';

        toast.error('Upgrade confirmation failed', {
          description,
        });
      } finally {
        navigate('/profile', { replace: true });
      }
    };

    if (hostedPageId) {
      void syncSubscription();
    } else {
      navigate('/profile', { replace: true });
    }
  }, [searchParams, navigate]);

  return null;
};

export default BillingCallbackPage;
