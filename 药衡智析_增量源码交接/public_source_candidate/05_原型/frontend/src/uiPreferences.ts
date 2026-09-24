export type UiPreferences = {
  density: 'comfortable' | 'compact';
  motion: 'system' | 'reduce';
  defaultBasis: 'unit' | 'total';
  taskNotifications: boolean;
};

export const UI_PREFERENCES_KEY = 'yaoheng.ui-preferences.v1';
export const DEFAULT_UI_PREFERENCES: UiPreferences = {
  density: 'comfortable', motion: 'system', defaultBasis: 'unit', taskNotifications: false,
};

/** Store presentation preferences only. Credentials and cost data never enter this key. */
export function readUiPreferences(): UiPreferences {
  try {
    const value = JSON.parse(localStorage.getItem(UI_PREFERENCES_KEY) ?? '{}');
    return {
      density: value.density === 'compact' ? 'compact' : 'comfortable',
      motion: value.motion === 'reduce' ? 'reduce' : 'system',
      defaultBasis: value.defaultBasis === 'total' ? 'total' : 'unit',
      taskNotifications: value.taskNotifications === true,
    };
  } catch { return { ...DEFAULT_UI_PREFERENCES }; }
}

export function saveUiPreferences(value: UiPreferences): boolean {
  try { localStorage.setItem(UI_PREFERENCES_KEY, JSON.stringify(value)); return true; }
  catch { return false; }
}
