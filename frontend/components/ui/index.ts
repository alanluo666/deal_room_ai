/**
 * Barrel file preserving the legacy `@/components/ui` import surface
 * (Button, Input, Label, Card, FieldError) used across the app. New
 * primitives are exported from their own paths (e.g. `@/components/ui/dialog`).
 */

export { Button } from "./button";
export type { ButtonProps, ButtonVariant, ButtonSize } from "./button";
export { Card } from "./card";
export { Input } from "./input";
export { Label } from "./label";
export { FieldError } from "./field-error";
