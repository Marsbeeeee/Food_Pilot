import type {
  FoodLogBrandGroup,
  FoodLogEntry,
  FoodLogPrimaryCategory,
} from '../types/types';

export interface FoodLogHierarchyBrandGroup extends FoodLogBrandGroup {
  entries: FoodLogEntry[];
  itemCount: number;
}

export interface FoodLogHierarchyCategory extends FoodLogPrimaryCategory {
  brands: FoodLogHierarchyBrandGroup[];
  itemCount: number;
}

const DEFAULT_CATEGORY: FoodLogPrimaryCategory = {
  id: 'other',
  name: '其他',
  sortOrder: 999,
};

const ALL_FOOD_CATEGORY: FoodLogPrimaryCategory = {
  id: 'all_food',
  name: '全部饮食',
  sortOrder: 0,
};

const DEFAULT_BRAND_GROUP: FoodLogBrandGroup = {
  id: 'unknown_source',
  name: '来源未明确',
  type: 'unknown_source',
  sortOrder: 999,
};

export function buildFoodLogHierarchy(entries: FoodLogEntry[]): FoodLogHierarchyCategory[] {
  const categoryMap = new Map<
  string,
  {
    category: FoodLogPrimaryCategory;
    itemCount: number;
    brands: Map<string, FoodLogHierarchyBrandGroup>;
  }
  >();

  entries.forEach((entry) => {
    const category = entry.category ?? DEFAULT_CATEGORY;
    const brandGroup = entry.brandGroup ?? DEFAULT_BRAND_GROUP;

    let categoryBucket = categoryMap.get(category.id);
    if (!categoryBucket) {
      categoryBucket = {
        category,
        itemCount: 0,
        brands: new Map(),
      };
      categoryMap.set(category.id, categoryBucket);
    }
    categoryBucket.itemCount += 1;

    const existingBrandGroup = categoryBucket.brands.get(brandGroup.id);
    if (existingBrandGroup) {
      existingBrandGroup.entries.push(entry);
      existingBrandGroup.itemCount += 1;
      return;
    }

    categoryBucket.brands.set(brandGroup.id, {
      ...brandGroup,
      entries: [entry],
      itemCount: 1,
    });
  });

  const categories = Array.from(categoryMap.values())
    .map(({ category, itemCount, brands }) => ({
      ...category,
      itemCount,
      brands: Array.from(brands.values()).sort(compareBrandGroups),
    }))
    .sort(compareCategories);

  if (entries.length === 0) {
    return categories;
  }

  return [
    {
      ...ALL_FOOD_CATEGORY,
      itemCount: entries.length,
      brands: buildBrandGroups(entries),
    },
    ...categories,
  ];
}

function compareCategories(
  left: FoodLogHierarchyCategory,
  right: FoodLogHierarchyCategory,
): number {
  return compareBySortOrder(left.sortOrder, right.sortOrder)
    || right.itemCount - left.itemCount
    || left.name.localeCompare(right.name, 'zh-CN');
}

function compareBrandGroups(
  left: FoodLogHierarchyBrandGroup,
  right: FoodLogHierarchyBrandGroup,
): number {
  return compareBySortOrder(left.sortOrder, right.sortOrder)
    || right.itemCount - left.itemCount
    || left.name.localeCompare(right.name, 'zh-CN');
}

function compareBySortOrder(left?: number, right?: number): number {
  const normalizedLeft = Number.isFinite(left) ? Number(left) : Number.MAX_SAFE_INTEGER;
  const normalizedRight = Number.isFinite(right) ? Number(right) : Number.MAX_SAFE_INTEGER;
  return normalizedLeft - normalizedRight;
}

function buildBrandGroups(entries: FoodLogEntry[]): FoodLogHierarchyBrandGroup[] {
  const brandMap = new Map<string, FoodLogHierarchyBrandGroup>();

  entries.forEach((entry) => {
    const brandGroup = entry.brandGroup ?? DEFAULT_BRAND_GROUP;
    const existingBrandGroup = brandMap.get(brandGroup.id);
    if (existingBrandGroup) {
      existingBrandGroup.entries.push(entry);
      existingBrandGroup.itemCount += 1;
      return;
    }

    brandMap.set(brandGroup.id, {
      ...brandGroup,
      entries: [entry],
      itemCount: 1,
    });
  });

  return Array.from(brandMap.values()).sort(compareBrandGroups);
}
