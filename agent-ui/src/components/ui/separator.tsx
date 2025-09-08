"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface SeparatorProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: "horizontal" | "vertical"
  decorative?: boolean
  variant?: "default" | "thick" | "dashed" | "dotted" | "gradient"
  spacing?: "none" | "small" | "medium" | "large"
  fadeEdges?: boolean
  animated?: boolean
}

const Separator = React.forwardRef<HTMLDivElement, SeparatorProps>(
  (
    {
      className,
      orientation = "horizontal",
      decorative = true,
      variant = "default",
      spacing = "medium",
      fadeEdges = false,
      animated = false,
      ...props
    },
    ref
  ) => {
    // Spacing classes based on prop
    const spacingClasses = {
      none: "",
      small: orientation === "horizontal" ? "my-1" : "mx-1",
      medium: orientation === "horizontal" ? "my-3" : "mx-3",
      large: orientation === "horizontal" ? "my-5" : "mx-5"
    }

    // Style variations
    const variantClasses = {
      default: "bg-gray-200 dark:bg-gray-700",
      thick: orientation === "horizontal"
        ? "h-[2px] bg-gray-300 dark:bg-gray-600"
        : "w-[2px] bg-gray-300 dark:bg-gray-600",
      dashed: `${orientation === "horizontal" ? "h-[1px]" : "w-[1px]"} border-dashed ${
        orientation === "horizontal" ? "border-b" : "border-r"
      } border-gray-300 dark:border-gray-600`,
      dotted: `${orientation === "horizontal" ? "h-[1px]" : "w-[1px]"} border-dotted ${
        orientation === "horizontal" ? "border-b" : "border-r"
      } border-gray-300 dark:border-gray-600`,
      gradient: orientation === "horizontal"
        ? "h-[1px] bg-gradient-to-r from-transparent via-gray-300 to-transparent dark:via-gray-600"
        : "w-[1px] bg-gradient-to-b from-transparent via-gray-300 to-transparent dark:via-gray-600"
    }

    // Base classes for orientation
    const baseOrientationClasses = {
      horizontal: variant === "thick" ? "" : "h-[1px] w-full",
      vertical: variant === "thick" ? "" : "h-full w-[1px]"
    }

    // Edge fading effect
    const fadeClasses = fadeEdges
      ? orientation === "horizontal"
        ? "before:absolute before:left-0 before:top-0 before:h-full before:w-8 before:bg-gradient-to-r before:from-white before:to-transparent dark:before:from-gray-900 " +
          "after:absolute after:right-0 after:top-0 after:h-full after:w-8 after:bg-gradient-to-l after:from-white after:to-transparent dark:after:from-gray-900"
        : "before:absolute before:top-0 before:left-0 before:w-full before:h-8 before:bg-gradient-to-b before:from-white before:to-transparent dark:before:from-gray-900 " +
          "after:absolute after:bottom-0 after:left-0 after:w-full after:h-8 after:bg-gradient-to-t after:from-white after:to-transparent dark:after:from-gray-900"
      : ""

    // Animation classes for subtle movement
    const animationClasses = animated
      ? "transition-all duration-300 hover:opacity-70"
      : ""

    return (
      <div
        ref={ref}
        role={decorative ? "none" : "separator"}
        aria-orientation={decorative ? undefined : orientation}
        data-orientation={orientation}
        className={cn(
          "shrink-0",
          fadeEdges && "relative",
          baseOrientationClasses[orientation],
          variant === "default" || variant === "thick" ? variantClasses[variant] : "",
          variant === "dashed" || variant === "dotted" || variant === "gradient" ? variantClasses[variant] : "",
          spacingClasses[spacing],
          fadeClasses,
          animationClasses,
          className
        )}
        {...props}
      />
    )
  }
)

Separator.displayName = "Separator"

// Export a simplified horizontal separator for common use
export const HorizontalSeparator: React.FC<Omit<SeparatorProps, 'orientation'>> = (props) => (
  <Separator orientation="horizontal" {...props} />
)

// Export a simplified vertical separator for common use
export const VerticalSeparator: React.FC<Omit<SeparatorProps, 'orientation'>> = (props) => (
  <Separator orientation="vertical" {...props} />
)

// Export a gradient separator for special sections
export const GradientSeparator: React.FC<Omit<SeparatorProps, 'variant'>> = (props) => (
  <Separator variant="gradient" fadeEdges {...props} />
)

export { Separator }