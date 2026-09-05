import matplotlib.pyplot as plt
import numpy as np

def create_dataset_viz():
    # Data from LaTeX table
    stats = {
        "Duration (Minutes)": {
            "min": 3.07,    # 00:03:04
            "avg": 27.68,   # 00:27:41
            "max": 82.25,   # 01:22:15
            "total_label": "Total: 09:13:47"
        },
        "Segment Count": {
            "min": 27,
            "avg": 233.6,
            "max": 594,
            "total_label": "Total: 4672 Segments"
        }
    }

    fig, axes = plt.subplots(2, 1, figsize=(10, 10))
    
    colors = ["#3498db", "#e74c3c"]
    
    for i, (metric, values) in enumerate(stats.items()):
        ax = axes[i]
        
        # Draw a shaded box for the range
        ax.barh(y=1, width=values["max"]-values["min"], left=values["min"], height=0.25, color='gray', alpha=0.15, zorder=1)
        
        # Draw a horizontal line for the range
        ax.hlines(y=1, xmin=values["min"], xmax=values["max"], color='gray', linestyle='--', alpha=0.5, linewidth=2, zorder=2)
        
        # Plot markers for Min, Max
        ax.scatter([values["min"], values["max"]], [1, 1], color=colors[i], s=200, zorder=3, edgecolors='white', linewidth=1.5)
        
        # Plot a LARGE square marker for Average (The "Insider Box")
        ax.scatter([values["avg"]], [1], color=colors[i], s=1800, marker='s', zorder=4, label="Average", edgecolors='white', linewidth=3)
        
        # Annotate values
        ax.text(values["min"], 1.15, f"Min: {values['min']}", ha='center', va='bottom', fontweight='bold', fontsize=12)
        ax.text(values["max"], 1.15, f"Max: {values['max']}", ha='center', va='bottom', fontweight='bold', fontsize=12)
        ax.text(values["avg"], 0.82, f"Avg: {values['avg']}", ha='center', va='top', fontweight='bold', color=colors[i], fontsize=15)
        
        # Title and Labels
        ax.set_title(f"Dataset {metric}\n({values['total_label']})", fontsize=18, pad=35, fontweight='bold')
        ax.set_yticks([]) # Hide Y axis
        ax.set_xlabel(metric, fontsize=14, fontweight='bold')
        
        # Set margin and limits
        ax.set_xlim(values["min"] * 0.6, values["max"] * 1.1)
        ax.set_ylim(0.4, 1.6)
        
        # Cleanup spines
        for spine in ["left", "right", "top"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#cccccc")

    plt.suptitle("Benchmark Dataset Characteristics (20 Videos)", fontsize=22, y=1.02, fontweight='bold')
    
    # Use tight_layout with a rect to leave space for the suptitle
    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    plt.subplots_adjust(hspace=0.6) # Add space between stacked plots

    # Save the plot
    output_path = "dataset_stats_viz.png"
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    print(f"Dataset statistics visualization saved to {output_path}")

if __name__ == "__main__":
    create_dataset_viz()
