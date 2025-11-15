import type { PropsWithChildren } from 'react';
import { MotionConfig } from 'motion/react';

const MotionProvider = ({ children }: PropsWithChildren) => {
  return (
    <MotionConfig
      reducedMotion="user"
      transition={{
        duration: 0.45,
        ease: [0.16, 1, 0.3, 1],
        type: 'tween',
      }}
    >
      {children}
    </MotionConfig>
  );
};

export { MotionProvider };
