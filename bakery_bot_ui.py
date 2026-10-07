        except Exception:
            st.error("Something went wrong updating this. Please try again in a moment.")
        else:
            st.success("Updated! Your bot will now reflect today's availability.")


def owner_view():
    st.title("Loaf")
    st.caption("Set up your bakery's ordering chatbot")

    business_name = st.text_input("Business name")
    slug = st.text_input(
        "Web address name (letters/numbers only, no spaces)",
        placeholder="e.g. sweettreats"
    )
    password = st.text_input(
        "Password (create one if this is a new bot, or enter your existing password to edit it)",
        type="password"
    )

    menu_df = pd.DataFrame({
        "Item": [""],
        "Price": [0],
        "Ingredients": [""]
    })
    menu = st.data_editor(menu_df, num_rows="dynamic")
    contact = st.text_input("Contact email")
    address = st.text_input("Business address")

    fulfillment_options = st.selectbox(
        "Fulfillment options offered",
        ["Pickup only", "Delivery only", "Both pickup and delivery"]
    )

    delivery_info = st.text_area(
        "Delivery / pickup info",
        placeholder="e.g. Pickup available Tue-Sat 10am-6pm. Delivery within 5 miles, $5 fee."
    )
    faq_info = st.text_area(
        "FAQ / common questions",
        placeholder="e.g. Q: Do you offer gluten-free? A: Yes, ask about our GF options."
    )
    business_hours = st.text_input(
        "Business hours",
        placeholder="e.g. Tue-Sat 9am-7pm, closed Sun-Mon"
    )
    advance_notice = st.text_input(
        "Advance notice required for custom orders",
        placeholder="e.g. 48 hours"
    )
    sold_out_items = st.text_input(
        "Out of stock today (comma separated, leave blank if none)",
        placeholder="e.g. Red velvet cake, Croissants"
    )
    menu_photos = st.file_uploader(
        "Menu photos (optional)",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"]
    )
    social_link = st.text_input(
        "Instagram / website link (optional)",
        placeholder="e.g. instagram.com/yourbakery"
    )

    if menu_photos:
        st.write("Menu photo previews:")
        st.image(menu_photos, width=150)

    if st.button("Save My Bakery Bot"):
        at_position = contact.find("@")
        dot_position = contact.find(".")
        clean_slug, slug_error = normalize_and_validate_slug(slug)
        if slug_error:
            st.error(slug_error)
        elif at_position == -1 or dot_position < at_position:
            st.error("Please enter a valid email")
        elif not password:
            st.error("Please create or enter a password for this bot.")
        else:
            existing_business = get_business(clean_slug)

            if existing_business:
                stored_hash = existing_business.get("admin_password")
                if stored_hash != hash_password(password):
                    st.error("Incorrect password for this business. If this is your first time saving, choose a slug that isn't already taken.")
                    st.stop()
                password_hash = stored_hash
            else:
                password_hash = hash_password(password)

            if menu_photos:
                menu_photo_urls = upload_menu_photos(clean_slug, menu_photos)
            else:
                menu_photo_urls = (existing_business or {}).get("menu_photo_urls", [])

            business_data = {
                "slug": clean_slug,
                "business_name": business_name,
                "contact_email": contact,
                "address": address,
                "fulfillment_options": fulfillment_options,
                "delivery_info": delivery_info,
                "faq_info": faq_info,
                "business_hours": business_hours,
                "advance_notice": advance_notice,
                "sold_out_items": sold_out_items,
                "social_link": social_link,
                "menu": menu.to_dict(orient="records"),
                "menu_photo_urls": menu_photo_urls,
                "admin_password": password_hash
            }
            try:
                supabase.table("businesses").upsert(business_data, on_conflict="slug").execute()
            except Exception:
                st.error("Something went wrong saving your bot. Please try again in a moment.")
            else:
                st.success("Saved! Share this link with your customers:")
                st.code(f"https://bakery-bot.streamlit.app/?slug={clean_slug}")
                st.caption("Bookmark this link to quickly mark items sold out during the day, without opening this full form:")
                st.code(f"https://bakery-bot.streamlit.app/?mode=quickupdate&slug={clean_slug}")


if mode == "owner":
    owner_view()
elif mode == "quickupdate":
    quick_update_view()
else:
    customer_view()
