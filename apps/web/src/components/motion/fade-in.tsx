import { motion } from 'motion/react';
import { forwardRef, type ComponentPropsWithoutRef } from 'react';

type FadeInProps = ComponentPropsWithoutRef<typeof motion.div> & {
  delay?: number;
};

const FadeIn = forwardRef<HTMLDivElement, FadeInProps>(
  ({ delay = 0, initial, animate, exit, transition, children, ...rest }, ref) => {
    return (
      <motion.div
        ref={ref}
        initial={initial ?? { opacity: 0, y: 16 }}
        animate={animate ?? { opacity: 1, y: 0 }}
        exit={exit ?? { opacity: 0, y: -16 }}
        transition={{
          duration: 0.45,
          ease: [0.16, 1, 0.3, 1],
          delay,
          type: 'tween',
          ...transition,
        }}
        {...rest}
      >
        {children}
      </motion.div>
    );
  }
);

FadeIn.displayName = 'FadeIn';

export { FadeIn, type FadeInProps };
