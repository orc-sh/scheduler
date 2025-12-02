import { useState } from 'react';
import { useAuthStore } from '@/stores/auth-store';
import { FadeIn } from '@/components/motion/fade-in';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { User, Crown, Check, Trash2 } from 'lucide-react';
import { useSubscriptions, useUpdateSubscription } from '@/hooks/use-subscriptions';
import { useDeleteAccount } from '@/hooks/use-user';
import { PLAN_IDS, type PlanId } from '@/types';
import { toast } from 'sonner';
import api from '@/lib/api';

const ProfilePage = () => {
  const user = useAuthStore((state) => state.user);
  const {
    data: subscriptions,
    isLoading: isLoadingSubscriptions,
    error: subscriptionsError,
  } = useSubscriptions();
  const updateSubscription = useUpdateSubscription();
  const deleteAccount = useDeleteAccount();
  const [updatingSubscriptionId, setUpdatingSubscriptionId] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Get the first subscription (prefer active, but fall back to any subscription)
  // Users typically have one subscription per account
  const activeSubscription =
    subscriptions?.find((sub) => sub.status === 'active') || subscriptions?.[0];
  const currentPlanId = activeSubscription?.plan_id || PLAN_IDS.FREE;

  const handlePlanSwitch = async (newPlanId: PlanId) => {
    console.log('handlePlanSwitch called with:', { newPlanId, activeSubscription, subscriptions });

    // Check if subscriptions are still loading
    if (isLoadingSubscriptions) {
      toast('Loading subscriptions', {
        description: 'Please wait while we load your subscription information.',
      });
      return;
    }

    // Check if there was an error loading subscriptions
    if (subscriptionsError) {
      toast.error('Error loading subscriptions', {
        description:
          'Unable to load your subscription information. Please try refreshing the page.',
      });
      return;
    }

    // Check if subscription exists
    if (!activeSubscription) {
      toast.error('No subscription found', {
        description:
          'You need to create a account first. Each account automatically gets a free subscription.',
      });
      return;
    }

    // Check if already on the requested plan
    if (currentPlanId === newPlanId) {
      toast('Already on this plan', {
        description: `You are already on the ${newPlanId === PLAN_IDS.PRO ? 'Pro' : 'Free'} plan.`,
      });
      return;
    }

    console.log('Attempting to update subscription:', {
      subscriptionId: activeSubscription.id,
      currentPlanId,
      newPlanId,
    });

    // If upgrading to a paid plan, use Chargebee hosted page flow
    if (
      newPlanId === PLAN_IDS.PRO ||
      newPlanId === PLAN_IDS.PRO_YEARLY ||
      newPlanId === PLAN_IDS.FREE_YEARLY ||
      newPlanId === PLAN_IDS.FREE
    ) {
      setUpdatingSubscriptionId(activeSubscription.id);
      try {
        const callbackUrl = `${window.location.origin}/billing/callback`;

        const response = await api.post('/api/subscriptions/upgrade', {
          plan_id: newPlanId,
          callback_url: callbackUrl,
        });

        const url: string | undefined = response.data?.url;
        if (!url) {
          throw new Error('No upgrade URL returned from server.');
        }

        toast('Redirecting to payment', {
          description: 'You will be redirected to securely update your payment details.',
        });

        window.location.href = url;
      } catch (error: any) {
        console.error('Failed to create upgrade URL:', error);
        const description =
          error?.response?.data?.detail ||
          error?.message ||
          'An error occurred while starting the upgrade.';

        toast.error('Failed to start upgrade', {
          description,
        });
      } finally {
        setUpdatingSubscriptionId(null);
      }

      return;
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await deleteAccount.mutateAsync();
      toast('Account deleted', {
        description: 'Your account and all associated data have been permanently deleted.',
      });
    } catch (error: any) {
      console.error('Failed to delete account:', error);
      const errorMessage =
        error?.response?.data?.detail ||
        error?.message ||
        'An error occurred while deleting your account.';
      toast.error('Failed to delete account', {
        description: errorMessage,
      });
    } finally {
      setShowDeleteDialog(false);
    }
  };

  const plans = [
    {
      id: PLAN_IDS.FREE,
      name: 'Free',
      description: 'Perfect for getting started',
      features: ['Basic scheduling', 'Limited accounts', 'Community support'],
    },
    {
      id: PLAN_IDS.PRO,
      name: 'Pro',
      description: 'For power users and teams',
      features: [
        'Unlimited scheduling',
        'Unlimited accounts',
        'Priority support',
        'Advanced features',
      ],
      popular: true,
    },
  ];

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto space-y-8">
        <FadeIn>
          <h1 className="text-4xl font-bold">Profile</h1>
        </FadeIn>

        <FadeIn delay={0.2} className="max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Your Profile
              </CardTitle>
              <CardDescription>View and edit your profile information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Email</p>
                <p className="text-base font-semibold">{user?.email}</p>
              </div>

              {user?.user_metadata && Object.keys(user.user_metadata).length > 0 && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">
                    Profile Information
                  </p>
                  <div className="space-y-2">
                    {user.user_metadata.full_name && (
                      <div>
                        <p className="text-sm text-muted-foreground">Name</p>
                        <p className="text-base">{user.user_metadata.full_name}</p>
                      </div>
                    )}
                    {user.user_metadata.avatar_url && (
                      <div className="flex items-center gap-3">
                        <img
                          src={user.user_metadata.avatar_url}
                          alt="Avatar"
                          className="h-16 w-16 rounded-full"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
            <CardFooter className="flex flex-col gap-4 border-t pt-6">
              <div className="w-full">
                <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="destructive"
                      className="w-full"
                      disabled={deleteAccount.isPending}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Account
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                      <AlertDialogDescription className="space-y-2">
                        <p>
                          This action cannot be undone. This will permanently delete your account
                          and remove all associated data from our servers, including:
                        </p>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          <li>All your accounts</li>
                          <li>All subscriptions (will be cancelled in Chargebee)</li>
                          <li>All scheduled jobs and webhooks</li>
                          <li>All URLs and logs</li>
                          <li>All other associated data</li>
                        </ul>
                        <p className="font-semibold mt-2">
                          You will be logged out immediately after deletion.
                        </p>
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={handleDeleteAccount}
                        disabled={deleteAccount.isPending}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      >
                        {deleteAccount.isPending ? 'Deleting...' : 'Yes, delete my account'}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </CardFooter>
          </Card>
        </FadeIn>

        <FadeIn delay={0.4}>
          <div>
            <h2 className="text-2xl font-bold mb-4">Subscription Plans</h2>
            <div className="grid gap-6 md:grid-cols-2 max-w-4xl">
              {plans.map((plan) => {
                const isCurrentPlan = currentPlanId === plan.id;
                const isUpdating = updatingSubscriptionId === activeSubscription?.id;

                return (
                  <Card
                    key={plan.id}
                    className={`relative ${isCurrentPlan ? 'ring-2 ring-primary' : ''} ${
                      plan.popular ? 'border-primary' : ''
                    }`}
                  >
                    {plan.popular && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <Badge className="bg-primary">
                          <Crown className="h-3 w-3 mr-1" />
                          Popular
                        </Badge>
                      </div>
                    )}
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>{plan.name} Plan</span>
                        {isCurrentPlan && (
                          <Badge variant="secondary" className="ml-2">
                            Current
                          </Badge>
                        )}
                      </CardTitle>
                      <CardDescription>{plan.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {plan.features.map((feature, index) => (
                          <li key={index} className="flex items-center gap-2 text-sm">
                            <Check className="h-4 w-4 text-primary flex-shrink-0" />
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                    <CardFooter>
                      <Button
                        className="w-full"
                        variant={isCurrentPlan ? 'outline' : 'default'}
                        disabled={isCurrentPlan || isUpdating || isLoadingSubscriptions}
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          console.log('Button clicked:', {
                            planId: plan.id,
                            isCurrentPlan,
                            isUpdating,
                            isLoadingSubscriptions,
                          });
                          handlePlanSwitch(plan.id);
                        }}
                      >
                        {isUpdating
                          ? 'Switching...'
                          : isCurrentPlan
                            ? 'Current Plan'
                            : `Switch to ${plan.name}`}
                      </Button>
                      {!isCurrentPlan && !isUpdating && !isLoadingSubscriptions && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Click to switch to {plan.name} plan
                        </p>
                      )}
                    </CardFooter>
                  </Card>
                );
              })}
            </div>
            {subscriptionsError && (
              <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-md">
                <p className="text-sm text-destructive">
                  Error loading subscriptions:{' '}
                  {subscriptionsError instanceof Error
                    ? subscriptionsError.message
                    : 'Unknown error'}
                </p>
              </div>
            )}
            {!isLoadingSubscriptions && !activeSubscription && !subscriptionsError && (
              <div className="mt-4 p-4 bg-muted border rounded-md">
                <p className="text-sm text-muted-foreground">
                  No subscription found. Create a account to automatically get a free subscription.
                </p>
              </div>
            )}
            {activeSubscription && (
              <div className="mt-4 text-sm text-muted-foreground space-y-2">
                <p>
                  Status: <Badge variant="outline">{activeSubscription.status}</Badge>
                </p>
                <p>
                  Subscription ID:{' '}
                  <code className="text-xs bg-muted px-1 py-0.5 rounded">
                    {activeSubscription.id}
                  </code>
                </p>
                <p>
                  Current Plan: <Badge variant="secondary">{activeSubscription.plan_id}</Badge>
                </p>
                {activeSubscription.current_term_end && (
                  <p>
                    Current term ends:{' '}
                    {new Date(activeSubscription.current_term_end).toLocaleDateString()}
                  </p>
                )}
              </div>
            )}
          </div>
        </FadeIn>
      </div>
    </div>
  );
};

export default ProfilePage;
