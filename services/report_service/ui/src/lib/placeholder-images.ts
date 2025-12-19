import data from './placeholder-images.json';

/**
 * Represents a placeholder image.
 */
export interface ImagePlaceholder {
  id: string;
  description: string;
  imageUrl: string;
  imageHint: string;
}

/**
 * A list of placeholder images.
 */
export const PlaceHolderImages: ImagePlaceholder[] = data.placeholderImages;
