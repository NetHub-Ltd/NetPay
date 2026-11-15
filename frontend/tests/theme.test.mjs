import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { runInNewContext } from "node:vm";
import ts from "typescript";

const source = readFileSync(new URL("../lib/theme.ts", import.meta.url), "utf8");
const compiled = ts.transpile(source, {
  module: ts.ModuleKind.ESNext,
  target: ts.ScriptTarget.ES2022,
});
const theme = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
const {
  applyTheme,
  getStoredTheme,
  isThemeId,
  PRODUCT_THEME,
  THEME_INIT_SCRIPT,
  THEME_STORAGE_KEY,
} = theme;

function withGlobal(name, value, run) {
  const previous = Object.getOwnPropertyDescriptor(globalThis, name);
  Object.defineProperty(globalThis, name, { configurable: true, value });
  try {
    run();
  } finally {
    if (previous) Object.defineProperty(globalThis, name, previous);
    else delete globalThis[name];
  }
}

test("light is the default and only light or dark are valid themes", () => {
  assert.equal(PRODUCT_THEME, "light");
  assert.equal(isThemeId("light"), true);
  assert.equal(isThemeId("dark"), true);
  assert.equal(isThemeId("ledger"), false);
  assert.equal(isThemeId(null), false);

  withGlobal("window", undefined, () => {
    assert.equal(getStoredTheme(), "light");
  });
});

test("stored preference accepts only current theme values and safely defaults on storage errors", () => {
  withGlobal("window", { localStorage: { getItem: () => "dark" } }, () => {
    assert.equal(getStoredTheme(), "dark");
  });
  withGlobal("window", { localStorage: { getItem: () => "shamba" } }, () => {
    assert.equal(getStoredTheme(), "light");
  });
  withGlobal("window", {
    localStorage: {
      getItem() {
        throw new Error("storage unavailable");
      },
    },
  }, () => {
    assert.equal(getStoredTheme(), "light");
  });
});

test("pre-paint script restores only supported preferences and defaults to light", () => {
  for (const [stored, expected] of [["dark", "dark"], ["light", "light"], ["harbor", "light"], [null, "light"]]) {
    const root = {
      theme: "",
      setAttribute(name, value) {
        if (name === "data-theme") this.theme = value;
      },
    };
    runInNewContext(THEME_INIT_SCRIPT, {
      localStorage: { getItem: (key) => (key === THEME_STORAGE_KEY ? stored : null) },
      document: { documentElement: root },
    });
    assert.equal(root.theme, expected);
  }
});

test("theme changes apply when storage is unavailable and persist when it works", () => {
  const root = {
    theme: "",
    setAttribute(name, value) {
      if (name === "data-theme") this.theme = value;
    },
  };
  withGlobal("document", { documentElement: root }, () => {
    withGlobal("window", {
      localStorage: {
        setItem(key, value) {
          assert.equal(key, THEME_STORAGE_KEY);
          assert.equal(value, "dark");
        },
      },
    }, () => {
      applyTheme("dark");
      assert.equal(root.theme, "dark");
    });

    withGlobal("window", {
      localStorage: {
        setItem() {
          throw new Error("storage unavailable");
        },
      },
    }, () => {
      applyTheme("light");
      assert.equal(root.theme, "light");
    });
  });
});
