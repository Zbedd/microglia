def test_imports():
    import microglia_pipeline  # package root
    from microglia_pipeline import io_nd2, preprocess, config  # essential modules only
    assert io_nd2 and preprocess and config
    
