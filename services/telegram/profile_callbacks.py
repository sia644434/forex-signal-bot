from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from analysis.styles import list_analysis_styles
from profiles import PRESET_PROFILES, create_profile, list_profiles, set_active_profile
from services.telegram.i18n import t


def presets_keyboard(language: str):
    labels = {
        "preset_scalping": "🔥 اسکلپ" if language == "fa" else "🔥 Scalping",
        "preset_swing": "📈 سوئینگ" if language == "fa" else "📈 Swing",
        "preset_day_trading": "☀️ دی‌تریدینگ" if language == "fa" else "☀️ Day Trading",
        "preset_trend": "📊 دنبال‌کننده روند" if language == "fa" else "📊 Trend Following",
    }
    rows = [[InlineKeyboardButton(labels[key], callback_data=f"profile_preset:{key}")] for key in PRESET_PROFILES]
    rows.append([InlineKeyboardButton("🛠 شخصی‌سازی" if language == "fa" else "🛠 Customize", callback_data="profile_customize")])
    rows.append([InlineKeyboardButton(t(language, "back"), callback_data="settings")])
    return InlineKeyboardMarkup(rows)


def style_keyboard(selected: set[str], language: str):
    rows = []
    for style in list_analysis_styles():
        title = style.title_fa if language == "fa" else style.title_en
        mark = "☑️" if style.style_id in selected else "☐"
        rows.append([InlineKeyboardButton(f"{mark} {title}", callback_data=f"profile_style_{style.style_id}")])
    rows.append([InlineKeyboardButton("✅ تأیید انتخاب" if language == "fa" else "✅ Confirm selection", callback_data="profile_confirm")])
    rows.append([InlineKeyboardButton(t(language, "back"), callback_data="profile_create")])
    return InlineKeyboardMarkup(rows)


def profile_list_keyboard(state, language: str):
    rows = []
    for profile in list_profiles(state):
        marker = "🟢" if profile.profile_id == state.settings.get("active_profile_id") else "⚪"
        rows.append([InlineKeyboardButton(f"{marker} {profile.name}", callback_data=f"profile_activate:{profile.profile_id}")])
    rows.append([InlineKeyboardButton("➕ ساخت پروفایل" if language == "fa" else "➕ Create profile", callback_data="profile_create")])
    rows.append([InlineKeyboardButton(t(language, "back"), callback_data="settings")])
    return InlineKeyboardMarkup(rows)


async def handle_profile_callback(query, state, language: str, data: str) -> bool:
    if data in {"settings_profiles", "profile_create"}:
        await query.edit_message_text(
            "⚙️ <b>ساخت پروفایل تحلیل</b>\n\nابتدا یک سبک آماده انتخاب کنید یا وارد شخصی‌سازی شوید."
            if language == "fa" else
            "⚙️ <b>Analysis Profile</b>\n\nChoose a ready-made profile or customize the analysis styles.",
            parse_mode="HTML", reply_markup=presets_keyboard(language))
        return True

    if data.startswith("profile_preset:"):
        preset = PRESET_PROFILES.get(data.split(":", 1)[1])
        if preset is None:
            await query.edit_message_text("❌ پروفایل آماده نامعتبر است." if language == "fa" else "❌ Invalid profile preset.")
            return True
        profile = create_profile(
            state, preset.name, [item.style_id for item in preset.styles],
            timeframes=preset.timeframes, schedule_seconds=preset.schedule_seconds)
        await query.edit_message_text(
            f"✅ پروفایل «{profile.name}» ساخته شد.\n\nسبک: {', '.join(item.style_id for item in profile.styles)}\nتایم‌فریم: {', '.join(profile.timeframes)}"
            if language == "fa" else
            f"✅ Profile “{profile.name}” created.\n\nStyle: {', '.join(item.style_id for item in profile.styles)}\nTimeframes: {', '.join(profile.timeframes)}",
            parse_mode="HTML", reply_markup=profile_list_keyboard(state, language))
        return True

    if data == "profile_customize":
        selected = set(state.settings.get("profile_style_selection", []))
        await query.edit_message_text(
            "🛠 <b>انتخاب سبک‌های تحلیل</b>\n\nمی‌توانید یک یا چند سبک را انتخاب کنید:"
            if language == "fa" else
            "🛠 <b>Choose Analysis Styles</b>\n\nSelect one or more styles:",
            parse_mode="HTML", reply_markup=style_keyboard(selected, language))
        return True

    if data.startswith("profile_style_"):
        style_id = data.removeprefix("profile_style_")
        if style_id not in {style.style_id for style in list_analysis_styles()}:
            await query.edit_message_text("❌ سبک تحلیل نامعتبر است." if language == "fa" else "❌ Invalid analysis style.")
            return True
        selected = set(state.settings.get("profile_style_selection", []))
        if style_id in selected:
            selected.remove(style_id)
        else:
            selected.add(style_id)
        state.settings["profile_style_selection"] = sorted(selected)
        await query.edit_message_reply_markup(reply_markup=style_keyboard(selected, language))
        return True

    if data == "profile_confirm":
        selected = list(dict.fromkeys(state.settings.get("profile_style_selection", [])))
        if not selected:
            await query.edit_message_text("⚠️ حداقل یک سبک را انتخاب کنید." if language == "fa" else "⚠️ Select at least one style.", reply_markup=style_keyboard(set(), language))
            return True
        profile = create_profile(state, "شخصی" if language == "fa" else "Custom", selected)
        state.settings.pop("profile_style_selection", None)
        await query.edit_message_text(
            f"✅ پروفایل شخصی ساخته شد.\n\nسبک‌ها: {', '.join(selected)}"
            if language == "fa" else
            f"✅ Custom profile created.\n\nStyles: {', '.join(selected)}",
            parse_mode="HTML", reply_markup=profile_list_keyboard(state, language))
        return True

    if data.startswith("profile_activate:"):
        profile_id = data.split(":", 1)[1]
        try:
            profile = set_active_profile(state, profile_id)
        except KeyError:
            await query.edit_message_text("❌ پروفایل پیدا نشد." if language == "fa" else "❌ Profile not found.")
            return True
        await query.edit_message_text(
            f"🟢 پروفایل فعال: <b>{profile.name}</b>\n\nنسخه: {profile.version}\nسبک‌ها: {', '.join(item.style_id for item in profile.styles)}"
            if language == "fa" else
            f"🟢 Active profile: <b>{profile.name}</b>\n\nVersion: {profile.version}\nStyles: {', '.join(item.style_id for item in profile.styles)}",
            parse_mode="HTML", reply_markup=profile_list_keyboard(state, language))
        return True

    return False
