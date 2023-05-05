import setuptools

setuptools.setup(
    name="meteoreo",
    version="0.1",
    author="Anavi Uppal",
    author_email="anavi.uppal@yale.edu",
    description="Predicts the number of meteors visible per hour.",
    packages=["meteoreo"],
    python_requires='>=3',
    install_requires=["numpy","pandas","ephem","datetime","streamlit","matplotlib","PIL","folium","streamlit_folium"]
)