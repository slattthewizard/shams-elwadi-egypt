import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    navTitle: z.string().optional(),
    metaTitle: z.string().optional(),
    metaDescription: z.string(),
    primaryKeyword: z.string().optional(),
    secondaryKeywords: z.string().optional(),
    publishedDate: z.string(),
    updatedDate: z.string().optional(),
    tag: z.string().optional(),
    subtitle: z.string().optional(),
    canonical: z.string().optional(),
    ogImage: z.string().optional(),
    faq: z.array(z.object({
      question: z.string(),
      answer: z.string(),
    })).optional(),
  }),
});

export const collections = { blog };
