/** @odoo-module **/
import { xml, Component, useState} from "@odoo/owl";
import { registry } from "@web/core/registry";
const fieldRegistry = registry.category("fields");

export class ImageField extends Component {
    static components = { };
    static template = "MultipleImage";
    static props = ["*"]

    setup() {
        super.setup();
        const { record, name } = this.props;
        this.state = useState({
            imageIds: record?.data?.[name]?._currentIds || []
        })
    }
}

export const imageField = {
    component: ImageField,
};

fieldRegistry.add("MultipleImage", imageField);
